import anthropic
import base64
import json
from django.conf import settings
from pathlib import Path


ANALYSIS_PROMPT = """
Tu es un expert en recyclage et en valorisation des déchets en Haïti.
Analyse cette image d'un déchet et retourne UNIQUEMENT un objet JSON valide (sans markdown, sans backticks) avec cette structure exacte :

{
  "category": "Nom de la catégorie (ex: Plastique PET, Métal ferreux, Carton, Électronique, Verre, Pneu usagé, Autre)",
  "category_slug": "slug de la catégorie (plastic, metal, paper, electronics, glass, tires, other)",
  "recyclability_score": <nombre entre 0 et 10>,
  "condition": "Très bon / Bon / Moyen / Mauvais",
  "estimated_weight_kg": <estimation du poids en kg, un nombre>,
  "estimated_value_htg": <valeur estimée en Gourdes haïtiennes, un nombre>,
  "estimated_value_usd": <valeur estimée en USD, un nombre>,
  "description": "Description détaillée du déchet visible sur l'image",
  "recommendations": "Recommandations de traitement et de recyclage",
  "confidence": <niveau de confiance entre 0 et 1>,
  "is_recyclable": <true ou false>,
  "hazardous": <true si matière dangereuse, sinon false>
}

Si l'image ne montre pas clairement un déchet ou un matériau recyclable, retourne :
{"error": "Image non valide ou déchet non identifiable", "is_recyclable": false}

Adapte les valeurs économiques au contexte haïtien (marché local de recyclage).
"""


class WasteAIService:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def analyze_image_from_file(self, image_path: str) -> dict:
        with open(image_path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')
        ext = Path(image_path).suffix.lower()
        media_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
        }
        media_type = media_type_map.get(ext, 'image/jpeg')
        return self._call_claude(image_data, media_type)

    def analyze_image_from_base64(self, base64_data: str, media_type: str = 'image/jpeg') -> dict:
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        return self._call_claude(base64_data, media_type)

    def analyze_image_from_url(self, url: str) -> dict:
        import urllib.request
        import urllib.error
        try:
            with urllib.request.urlopen(url) as response:
                image_data = base64.standard_b64encode(response.read()).decode('utf-8')
                content_type = response.headers.get('Content-Type', 'image/jpeg')
                media_type = content_type.split(';')[0].strip()
            return self._call_claude(image_data, media_type)
        except urllib.error.URLError as e:
            return {'error': f"Impossible de charger l'image: {str(e)}"}

    def _call_claude(self, image_data: str, media_type: str) -> dict:
        raw_response = ''
        try:
            message = self.client.messages.create(
                model='claude-opus-4-5',
                max_tokens=1024,
                messages=[
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'image',
                                'source': {
                                    'type': 'base64',
                                    'media_type': media_type,
                                    'data': image_data,
                                },
                            },
                            {
                                'type': 'text',
                                'text': ANALYSIS_PROMPT,
                            },
                        ],
                    }
                ],
            )
            raw_response = message.content[0].text.strip()
            if raw_response.startswith('```'):
                raw_response = raw_response.split('```')[1]
                if raw_response.startswith('json'):
                    raw_response = raw_response[4:]
            return json.loads(raw_response)
        except json.JSONDecodeError:
            return {'error': 'Réponse AI non parseable', 'raw': raw_response}
        except Exception as e:
            return {'error': f'Erreur API Claude: {str(e)}'}


class _LazyAIService:
    """Proxy lazy — n'instancie WasteAIService qu'au premier appel."""
    _instance = None

    def __getattr__(self, name):
        if _LazyAIService._instance is None:
            _LazyAIService._instance = WasteAIService()
        return getattr(_LazyAIService._instance, name)


ai_service = _LazyAIService()
