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

    # ── Extraction + normalisation JSON ─────────────────────────────────────

    @staticmethod
    def _parse_json_response(raw: str) -> dict:
        text = raw.strip()

        if '```' in text:
            for part in text.split('```'):
                candidate = part.lstrip('json').strip()
                if candidate.startswith('{'):
                    text = candidate
                    break

        start = text.find('{')
        end   = text.rfind('}')
        if start != -1 and end != -1:
            text = text[start:end + 1]

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return {'error': 'Réponse agent non parseable', 'raw': raw}

        return ManagedAgentService._normalize(data)

    # Mots-clés → slug de catégorie (ordre de priorité décroissant)
    _SLUG_KEYWORDS = [
        (['pet', 'plastique', 'hdpe', 'pvc', 'pp ', 'polyet', 'polyprop', 'plastic'], 'plastic'),
        (['métal', 'metal', 'fer', 'acier', 'aluminium', 'cuivre', 'ferreux', 'zinc'],  'metal'),
        (['papier', 'carton', 'paper', 'journal', 'kraft'],                              'paper'),
        (['électronique', 'electronic', 'deee', 'e-waste', 'circuit', 'batterie'],       'electronics'),
        (['verre', 'glass'],                                                              'glass'),
        (['pneu', 'tire', 'caoutchouc'],                                                 'tires'),
    ]

    @classmethod
    def _slug_from_name(cls, name: str) -> str:
        lower = name.lower()
        for keywords, slug in cls._SLUG_KEYWORDS:
            if any(kw in lower for kw in keywords):
                return slug
        return 'other'

    @staticmethod
    def _pick(data: dict, *keys, default=None):
        """Retourne la première valeur non-nulle parmi les clés données."""
        for k in keys:
            v = data.get(k)
            if v is not None:
                return v
        return default

    @staticmethod
    def _normalize(data: dict) -> dict:
        """
        Convertit la réponse de l'agent (format variable) vers le format
        attendu par les vues, templates et la tâche Celery.

        Champs garantis en sortie :
          category, category_slug, recyclability_score, condition,
          estimated_weight_kg, estimated_value_htg, estimated_value_usd,
          description, recommendations, confidence, is_recyclable,
          hazardous, summary, material_type
        """
        # ── Déjà au bon format canonique ────────────────────────────────────
        if 'estimated_value_htg' in data:
            data.setdefault('summary',       data.get('description', '')[:120])
            data.setdefault('material_type', data.get('category', ''))
            return data

        pick = ManagedAgentService._pick

        # ── Matériaux (noms de clé observés : materiaux / materiaux_detectes /
        #    materials_detected) ─────────────────────────────────────────────
        materials = pick(data, 'materiaux', 'materials_detected', 'materiaux_detectes', default=[])
        dominant  = materials[0] if materials else {}

        # Catégorie
        category_name = (
            dominant.get('type')
            or data.get('category')
            or data.get('categorie_dechet')
            or 'Déchet recyclable'
        )
        category_slug = ManagedAgentService._slug_from_name(category_name)

        # ── Helpers de recherche numérique ───────────────────────────────────
        def num(obj, *keys):
            """Retourne le premier nombre trouvé parmi les clés d'un dict."""
            if not isinstance(obj, dict):
                return None
            for k in keys:
                v = obj.get(k)
                if isinstance(v, (int, float)):
                    return float(v)
                if isinstance(v, dict):
                    # Cherche 'moyenne', 'moyen', 'max', 'min', 'valeur' dans le sous-dict
                    inner = num(v, 'moyenne', 'moyen', 'max', 'min', 'valeur')
                    if inner is not None:
                        return inner
            return None

        def mat_sum(key, *aliases):
            """Somme une valeur numérique sur tous les matériaux (clé variable)."""
            total = 0.0
            for m in materials:
                v = num(m, key, *aliases)
                if v is not None:
                    total += v
            return total or None

        # Poids ───────────────────────────────────────────────────────────────
        summary_obj = data.get('summary', {}) if isinstance(data.get('summary'), dict) else {}
        poids_obj   = data.get('estimation_poids', {})

        weight = (
            num(summary_obj, 'total_estimated_weight_kg')
            or num(poids_obj, 'valeur_kg', 'fourchette_max_kg')
            or num(data, 'poids_total_estime_kg', 'total_weight_kg')
            or mat_sum('estimated_weight_kg', 'poids_estime_kg', 'weight_kg')
            or 0
        )

        # Valeurs HTG ─────────────────────────────────────────────────────────
        # Formats observés :
        #  F1 valeur_marchande_htg.valeur_estimee_centrale
        #  F2 summary.total_value_htg
        #  F3 valeur_marchande.valeur_totale_htg.{moyenne|max}
        #  F4 valeur_totale_estimee.htg   +   materiaux[].valeur_estimee_htg
        vm     = data.get('valeur_marchande', {})
        vte    = data.get('valeur_totale_estimee', {})

        value_htg = (
            num(summary_obj, 'total_value_htg', 'valeur_totale_htg')
            or num(data.get('valeur_marchande_htg', {}), 'valeur_estimee_centrale', 'valeur_totale_max')
            or num(vm.get('valeur_totale_htg', {}) if isinstance(vm.get('valeur_totale_htg'), dict) else vm,
                   'moyenne', 'moyen', 'max')
            or num(vte, 'htg')
            or mat_sum('estimated_value_htg', 'valeur_estimee_htg')
            or 0
        )

        # Valeurs USD ─────────────────────────────────────────────────────────
        value_usd = (
            num(summary_obj, 'total_value_usd', 'valeur_totale_usd')
            or num(data.get('valeur_marchande_usd', {}), 'valeur_estimee_centrale')
            or num(vm.get('valeur_totale_usd', {}) if isinstance(vm.get('valeur_totale_usd'), dict) else vm,
                   'moyenne', 'moyen', 'max')
            or num(vte, 'usd')
            or mat_sum('estimated_value_usd', 'valeur_estimee_usd')
            or 0
        )

        # Score recyclabilité ─────────────────────────────────────────────────
        confidence    = float(data.get('confidence', 0.5))
        is_recyclable = bool(data.get('is_recyclable', True))
        recyclability_score = (
            max(1, round(confidence * 10)) if is_recyclable
            else max(0, round(confidence * 3))
        )

        # Condition ───────────────────────────────────────────────────────────
        condition_raw = pick(dominant, 'etat', 'condition', 'detail_etat', default='Moyen')
        _CMAP = {
            'très bon': 'Très bon', 'tres bon': 'Très bon', 'excellent': 'Très bon',
            'bon': 'Bon', 'good': 'Bon', 'utilisé': 'Bon',
            'moyen': 'Moyen', 'medium': 'Moyen', 'mixte': 'Moyen',
            'passable': 'Moyen', 'usagé': 'Moyen', 'used': 'Moyen',
            'mauvais': 'Mauvais', 'poor': 'Mauvais', 'bad': 'Mauvais',
        }
        # Prend le premier mot pour la correspondance si valeur composée
        key = str(condition_raw).lower().split(' —')[0].split(',')[0].strip()
        condition = _CMAP.get(key, str(condition_raw).capitalize()[:40])

        # Description ─────────────────────────────────────────────────────────
        desc_parts = []
        for m in materials:
            d = m.get('description') or m.get('sous_type') or m.get('detail_etat') or ''
            if d:
                desc_parts.append(d)
        description = ' — '.join(desc_parts) if desc_parts else category_name

        # Recommandations ─────────────────────────────────────────────────────
        reco_raw = (
            pick(data, 'recommandations', 'recommendations')
            or pick(summary_obj, 'recommended_action', 'recommended_actions')
            or ''
        )
        recommendations = (
            ' | '.join(reco_raw) if isinstance(reco_raw, list) else str(reco_raw)
        )

        # Matières dangereuses ────────────────────────────────────────────────
        danger    = pick(data, 'hazardous_materials', 'matieres_dangereuses', default={})
        hazardous = bool(pick(danger, 'detected', 'detectees', default=False))

        # Résumé ──────────────────────────────────────────────────────────────
        summary_str = (
            pick(summary_obj, 'recommended_action')
            or f"{round(weight)} kg de {category_name} — valeur estimée {round(value_htg)} HTG"
        )

        return {
            # ── Format canonique attendu par toute l'app ─────────────────────
            'category':            category_name,
            'category_slug':       category_slug,
            'recyclability_score': recyclability_score,
            'condition':           condition,
            'estimated_weight_kg': weight,
            'estimated_value_htg': value_htg,
            'estimated_value_usd': value_usd,
            'description':         description,
            'recommendations':     recommendations,
            'confidence':          confidence,
            'is_recyclable':       is_recyclable,
            'hazardous':           hazardous,
            'summary':             summary_str,
            'material_type':       category_name,
            # ── Données brutes pour debug / admin ─────────────────────────────
            '_details':            data,
        }


class _LazyService:
    """Instancie ManagedAgentService au premier appel (évite les imports circulaires)."""
    _instance = None

    def __getattr__(self, name):
        if _LazyService._instance is None:
            _LazyService._instance = ManagedAgentService()
        return getattr(_LazyService._instance, name)


class RecyclingAdvisor:
    """
    Agent conversationnel Conseiller Recyclage EcoCycle via Sessions API.
    Le system prompt est configuré directement sur l'agent dans la console Anthropic.
    Le session_id est retourné au client et réutilisé pour maintenir le contexte.
    """

    TIMEOUT = 60

    def __init__(self):
        self.client   = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.agent_id = settings.ANTHROPIC_ADVISOR_AGENT_ID
        self.env_id   = settings.ANTHROPIC_ENV_ID

    def chat(self, user_message: str, session_id: str = None) -> tuple:
        """
        Retourne (reply, session_id).
        session_id=None → crée une nouvelle session (premier message).
        session_id fourni → continue la conversation existante.
        """
        if not self.agent_id or not self.env_id:
            return 'Agent non configuré (ANTHROPIC_ADVISOR_AGENT_ID manquant).', None

        if not session_id:
            try:
                session    = self.client.beta.sessions.create(
                    agent=self.agent_id,
                    environment_id=self.env_id,
                )
                session_id = session.id
            except Exception as e:
                return f'Erreur création session : {e}', None

        collected_text = []
        done           = threading.Event()
        stream_error   = [None]

        def stream_loop():
            try:
                for event in self.client.beta.sessions.events.stream(session_id):
                    if event.type == 'agent.message':
                        for block in event.content:
                            if block.type == 'text':
                                collected_text.append(block.text)
                    elif event.type in ('session.status_idle', 'session.status_terminated'):
                        done.set()
                        return
                    elif event.type == 'session.error':
                        stream_error[0] = (
                            f"{getattr(event.error, 'type', '?')}: "
                            f"{getattr(event.error, 'message', '')}"
                        )
                        done.set()
                        return
            except Exception as e:
                stream_error[0] = str(e)
                done.set()

        t = threading.Thread(target=stream_loop, daemon=True)
        t.start()

        try:
            self.client.beta.sessions.events.send(
                session_id,
                events=[{'type': 'user.message', 'content': [{'type': 'text', 'text': user_message}]}],
            )
        except Exception as e:
            done.set()
            return f'Erreur envoi message : {e}', None

        done.wait(timeout=self.TIMEOUT)
        t.join(timeout=5)

        if stream_error[0]:
            return f'Erreur agent : {stream_error[0]}', None

        reply = ''.join(collected_text) or 'Aucune réponse reçue.'
        return reply, session_id

    def quick_estimate(self, waste_description: str) -> str:
        """Estimation rapide d'un déchet sans photo."""
        reply, _ = self.chat(f"Estimation rapide : {waste_description}")
        return reply


ai_service        = _LazyService()
recycling_advisor = RecyclingAdvisor()
