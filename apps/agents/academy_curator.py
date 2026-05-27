import json
import logging
import urllib.request
import urllib.parse
from anthropic import Anthropic
from django.conf import settings

logger = logging.getLogger(__name__)

ACADEMY_CURATOR_SYSTEM_PROMPT = """
Tu es un expert en éducation environnementale et en recyclage.
Tu travailles pour EcoCycle Haiti — une plateforme de recyclage en Haïti.

Ta mission : Créer des cours complets et structurés en français
à partir de vidéos YouTube sur le recyclage et l'environnement.

CONTEXTE HAÏTIEN :
- Audience : citoyens haïtiens, revendeurs de déchets, collecteurs
- Langue principale : français (avec termes créoles si pertinent)
- Contexte économique : marché local, prix en HTG
- Déchets communs en Haïti : plastique PET, métal, carton, électronique

RÈGLES DE QUALITÉ :
1. Chaque cours doit avoir 3 à 6 leçons
2. Chaque leçon doit avoir des objectifs pédagogiques clairs
3. Le contenu doit être pratique et applicable localement
4. Adapter les exemples au contexte haïtien
5. Niveau de langue accessible (pas de jargon technique complexe)

RETOURNE UNIQUEMENT un JSON valide sans markdown ni backticks :
{
  "title": "Titre du cours accrocheur en français",
  "description": "Description complète du cours (150 mots min)",
  "level": "beginner|intermediate|advanced",
  "estimated_duration_minutes": 90,
  "tags": ["recyclage", "plastique", "haïti"],
  "category_slug": "plastic|metal|paper|electronics|glass|tires|other",
  "lessons": [
    {
      "title": "Titre de la leçon",
      "description": "Objectifs et contenu de la leçon (100 mots)",
      "video_url": "URL YouTube de la vidéo",
      "key_points": ["Point clé 1", "Point clé 2", "Point clé 3"],
      "duration_minutes": 15,
      "order": 1
    }
  ],
  "pdf_content": "# Titre du cours\\n\\n## Introduction\\n\\nContenu Markdown complet (500 mots min)...",
  "quiz_questions": [
    {
      "question": "Question de validation",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": 0,
      "explanation": "Explication de la bonne réponse"
    }
  ]
}
"""

SEARCH_QUERIES = [
    "recyclage plastique tutorial",
    "waste management Haiti environment",
    "économie circulaire formation",
    "recycling metal tutorial beginner",
    "environmental education Caribbean",
    "tri des déchets formation",
    "recyclage électronique e-waste tutorial",
    "compostage déchets organiques",
    "recyclage verre carton formation",
    "green economy developing countries tutorial",
]


def _strip_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith('```'):
        raw = raw.split('```')[1]
        if raw.startswith('json'):
            raw = raw[4:]
    return raw.strip()


class AcademyCuratorAgent:

    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.youtube_api_key = getattr(settings, 'YOUTUBE_API_KEY', None)

    def search_youtube_videos(self, query: str, max_results: int = 5) -> list:
        if not self.youtube_api_key:
            return self._mock_videos(query)

        params = urllib.parse.urlencode({
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': max_results,
            'order': 'relevance',
            'videoDuration': 'medium',
            'relevanceLanguage': 'fr',
            'key': self.youtube_api_key,
        })
        url = f'https://www.googleapis.com/youtube/v3/search?{params}'
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
            videos = []
            for item in data.get('items', []):
                snippet = item.get('snippet', {})
                video_id = item['id'].get('videoId', '')
                if not video_id:
                    continue
                stats = self._get_video_stats(video_id)
                videos.append({
                    'title': snippet.get('title', ''),
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'video_id': video_id,
                    'channel': snippet.get('channelTitle', ''),
                    'thumbnail': f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
                    'description': snippet.get('description', '')[:300],
                    'views': stats.get('views', 0),
                    'duration': stats.get('duration', ''),
                })
            return [v for v in videos if v['views'] > 500]
        except Exception as exc:
            logger.error('YouTube API error: %s', exc)
            return []

    def _get_video_stats(self, video_id: str) -> dict:
        params = urllib.parse.urlencode({
            'part': 'statistics,contentDetails',
            'id': video_id,
            'key': self.youtube_api_key,
        })
        url = f'https://www.googleapis.com/youtube/v3/videos?{params}'
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
            item = data['items'][0] if data.get('items') else {}
            return {
                'views': int(item.get('statistics', {}).get('viewCount', 0)),
                'duration': item.get('contentDetails', {}).get('duration', ''),
            }
        except Exception:
            return {'views': 0, 'duration': ''}

    def _mock_videos(self, query: str) -> list:
        return [{
            'title': f'Tutoriel : {query}',
            'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'video_id': 'dQw4w9WgXcQ',
            'channel': 'EcoCycle Demo',
            'thumbnail': 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
            'description': f'Tutoriel complet sur {query} adapté au contexte haïtien.',
            'views': 15000,
            'duration': 'PT12M30S',
        }]

    def evaluate_and_group_videos(self, all_videos: list) -> list:
        response = self.client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=2048,
            system="""Tu es un expert en éducation sur le recyclage et l'environnement.
Analyse ces vidéos YouTube et regroupe-les en 2-3 cours cohérents pour EcoCycle Haiti.
Pour chaque groupe, évalue la pertinence (1-10). Ne garde que les groupes avec score >= 6.
Retourne UNIQUEMENT un JSON valide :
{
  "course_groups": [
    {
      "theme": "Thème du cours",
      "relevance_score": 8.5,
      "videos": [
        {"url": "url_youtube", "title": "titre", "relevance_score": 9.0, "why_relevant": "..."}
      ]
    }
  ]
}""",
            messages=[{
                'role': 'user',
                'content': (
                    f'Analyse et regroupe ces vidéos en cours sur le recyclage pour EcoCycle Haiti :\n\n'
                    f'{json.dumps(all_videos[:30], indent=2, ensure_ascii=False)}'
                ),
            }],
        )
        try:
            return json.loads(_strip_json(response.content[0].text)).get('course_groups', [])
        except Exception as exc:
            logger.error('evaluate_and_group_videos parse error: %s', exc)
            return []

    def generate_full_course(self, videos: list, theme: str) -> dict:
        response = self.client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=4096,
            system=ACADEMY_CURATOR_SYSTEM_PROMPT,
            messages=[{
                'role': 'user',
                'content': (
                    f'Crée un cours complet sur le thème : "{theme}"\n\n'
                    f'Basé sur ces vidéos YouTube :\n'
                    f'{json.dumps(videos, indent=2, ensure_ascii=False)}\n\n'
                    f'Le cours doit être adapté au contexte haïtien, inclure 3-5 leçons, '
                    f'un document PDF Markdown, et 5 questions de quiz.'
                ),
            }],
        )
        try:
            return json.loads(_strip_json(response.content[0].text))
        except Exception as exc:
            logger.error('generate_full_course parse error: %s', exc)
            raise

    def run(self) -> dict:
        from apps.academy.models import CourseRecommendation
        from apps.accounts.models import User
        from apps.notifications.models import Notification
        from apps.notifications.email_service import EmailService
        import random

        queries = random.sample(SEARCH_QUERIES, min(4, len(SEARCH_QUERIES)))
        all_videos = []
        for query in queries:
            all_videos.extend(self.search_youtube_videos(query, max_results=5))

        if not all_videos:
            return {'status': 'no_videos_found'}

        seen = set()
        unique_videos = []
        for v in all_videos:
            if v['video_id'] not in seen:
                seen.add(v['video_id'])
                unique_videos.append(v)

        course_groups = self.evaluate_and_group_videos(unique_videos)
        if not course_groups:
            return {'status': 'no_relevant_groups'}

        created = []
        for group in course_groups[:2]:
            if group.get('relevance_score', 0) < 6:
                continue
            try:
                course_data = self.generate_full_course(group['videos'], group['theme'])
                rec = CourseRecommendation.objects.create(
                    title=course_data.get('title', group['theme']),
                    description=course_data.get('description', ''),
                    level=course_data.get('level', 'beginner'),
                    youtube_videos=group['videos'],
                    suggested_lessons=course_data.get('lessons', []),
                    pdf_content=course_data.get('pdf_content', ''),
                    quiz_questions=course_data.get('quiz_questions', []),
                    estimated_duration_minutes=course_data.get('estimated_duration_minutes', 60),
                    tags=course_data.get('tags', []),
                    category_slug=course_data.get('category_slug', 'other'),
                    status='pending',
                )
                created.append(rec)
            except Exception as exc:
                logger.error('Course generation error: %s', exc)

        if not created:
            return {'status': 'generation_failed'}

        count = len(created)
        admins = User.objects.filter(role='admin', is_active=True)
        courses_html = ''.join(
            f'<li><b>{r.title}</b> — {r.get_level_display()} — {len(r.suggested_lessons)} leçons</li>'
            for r in created
        )
        frontend_url = settings.FRONTEND_URL.split(',')[0].strip().rstrip('/')

        for admin in admins:
            Notification.objects.create(
                user=admin,
                notification_type='system',
                title=f'🎓 {count} nouveau(x) cours suggéré(s) par l\'IA',
                message=(
                    f'L\'agent Academy a trouvé {count} formation(s) pertinente(s). '
                    f'Consultez les recommandations pour les approuver.'
                ),
                data={
                    'type': 'academy_recommendation',
                    'count': count,
                    'recommendation_ids': [str(r.id) for r in created],
                },
            )
            EmailService._send(
                admin.email,
                f'[EcoCycle Academy] {count} nouveau(x) cours à approuver',
                f'''<h2>🎓 Recommandations Academy IA</h2>
                <p>L\'agent Academy Curator a généré {count} nouveau(x) cours :</p>
                <ul>{courses_html}</ul>
                <p>
                    <a href="{frontend_url}/panel/recommendations/"
                       style="background:#0d7a45;color:white;padding:12px 24px;
                              border-radius:8px;text-decoration:none;">
                        Voir les recommandations →
                    </a>
                </p>''',
            )

        return {
            'status': 'success',
            'courses_generated': count,
            'titles': [r.title for r in created],
        }


academy_curator = AcademyCuratorAgent()
