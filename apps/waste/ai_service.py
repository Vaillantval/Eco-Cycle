import base64
import json
import threading
from pathlib import Path

import anthropic
from django.conf import settings


class ManagedAgentService:
    """
    Analyse de déchets via Anthropic Managed Agents (Sessions API).

    Interface identique à l'ancienne WasteAIService :
      analyze_image_from_file(path)
      analyze_image_from_base64(b64_data, media_type)
      analyze_image_from_url(url)
    """

    TIMEOUT = 90  # secondes max pour la réponse de l'agent

    def __init__(self):
        self.client   = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.agent_id = settings.ANTHROPIC_AGENT_ID
        self.env_id   = settings.ANTHROPIC_ENV_ID

    # ── Points d'entrée publics ──────────────────────────────────────────────

    def analyze_image_from_file(self, image_path: str) -> dict:
        with open(image_path, 'rb') as f:
            data = base64.standard_b64encode(f.read()).decode()
        ext = Path(image_path).suffix.lower()
        media_type = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.png': 'image/png',  '.webp': 'image/webp',
        }.get(ext, 'image/jpeg')
        return self._run_session([
            self._image_block_base64(data, media_type),
            self._text_block('Analyse ce déchet et retourne le JSON.'),
        ])

    def analyze_image_from_base64(self, base64_data: str, media_type: str = 'image/jpeg') -> dict:
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        return self._run_session([
            self._image_block_base64(base64_data, media_type),
            self._text_block('Analyse ce déchet et retourne le JSON.'),
        ])

    def analyze_image_from_url(self, url: str) -> dict:
        return self._run_session([
            self._image_block_url(url),
            self._text_block('Analyse ce déchet et retourne le JSON.'),
        ])

    # ── Construction des blocs ───────────────────────────────────────────────

    @staticmethod
    def _image_block_base64(data: str, media_type: str) -> dict:
        return {
            'type': 'image',
            'source': {'type': 'base64', 'data': data, 'media_type': media_type},
        }

    @staticmethod
    def _image_block_url(url: str) -> dict:
        return {'type': 'image', 'source': {'type': 'url', 'url': url}}

    @staticmethod
    def _text_block(text: str) -> dict:
        return {'type': 'text', 'text': text}

    # ── Logique de session ───────────────────────────────────────────────────

    def _run_session(self, content: list) -> dict:
        if not self.agent_id or not self.env_id:
            return {'error': 'Agent non configuré (ANTHROPIC_AGENT_ID / ANTHROPIC_ENV_ID manquants).'}

        # 1. Créer la session
        try:
            session = self.client.beta.sessions.create(
                agent=self.agent_id,
                environment_id=self.env_id,
            )
        except Exception as e:
            return {'error': f'Erreur création session : {e}'}

        session_id     = session.id
        collected_text = []
        done           = threading.Event()
        stream_error   = [None]

        # 2. Ouvrir le stream SSE dans un thread dédié
        def stream_loop():
            try:
                for event in self.client.beta.sessions.events.stream(session_id):
                    etype = event.type

                    if etype == 'agent.message':
                        for block in event.content:
                            if block.type == 'text':
                                collected_text.append(block.text)

                    elif etype in ('session.status_idle', 'session.status_terminated'):
                        done.set()
                        return

                    elif etype == 'session.error':
                        err = event.error
                        stream_error[0] = (
                            f"{getattr(err, 'type', 'unknown')}: "
                            f"{getattr(err, 'message', '')}"
                        )
                        done.set()
                        return

            except Exception as e:
                stream_error[0] = str(e)
                done.set()

        t = threading.Thread(target=stream_loop, daemon=True)
        t.start()

        # 3. Envoyer le message utilisateur (image + instruction)
        try:
            self.client.beta.sessions.events.send(
                session_id,
                events=[{'type': 'user.message', 'content': content}],
            )
        except Exception as e:
            done.set()
            return {'error': f'Erreur envoi message : {e}'}

        # 4. Attendre la réponse complète
        done.wait(timeout=self.TIMEOUT)
        t.join(timeout=5)

        if stream_error[0]:
            return {'error': f'Erreur agent : {stream_error[0]}'}

        if not collected_text:
            return {'error': 'Aucune réponse reçue (timeout ou session vide).'}

        return self._parse_json_response(''.join(collected_text))

    # ── Extraction JSON depuis la réponse Markdown ───────────────────────────

    @staticmethod
    def _parse_json_response(raw: str) -> dict:
        text = raw.strip()

        # Extraire depuis un bloc ```json ... ``` si présent
        if '```' in text:
            for part in text.split('```'):
                candidate = part.lstrip('json').strip()
                if candidate.startswith('{'):
                    text = candidate
                    break

        # Isoler le premier objet JSON {...}
        start = text.find('{')
        end   = text.rfind('}')
        if start != -1 and end != -1:
            text = text[start:end + 1]

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {'error': 'Réponse agent non parseable', 'raw': raw}


class _LazyService:
    """Instancie ManagedAgentService au premier appel (évite les imports circulaires)."""
    _instance = None

    def __getattr__(self, name):
        if _LazyService._instance is None:
            _LazyService._instance = ManagedAgentService()
        return getattr(_LazyService._instance, name)


ai_service = _LazyService()
