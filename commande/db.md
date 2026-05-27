# EcoCycle — Agent Academy Curator & Blog Writer

> **Objectif** : Deux agents IA autonomes qui génèrent automatiquement du contenu
> pour l'Academy et le Blog EcoCycle Haiti, avec approbation admin avant publication.

---

## PARTIE 1 — MODÈLES DE DONNÉES

### Dans apps/academy/models.py — Ajouter CourseRecommendation

```python
class CourseRecommendation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('published', 'Publié'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    level = models.CharField(
        max_length=20,
        choices=[('beginner','Débutant'),('intermediate','Intermédiaire'),('advanced','Avancé')],
        default='beginner'
    )
    youtube_videos = models.JSONField(default=list)
    # Structure :
    # [
    #   {
    #     "title": "Introduction au recyclage du plastique",
    #     "url": "https://youtube.com/watch?v=xxx",
    #     "video_id": "xxx",
    #     "channel": "Nom de la chaîne",
    #     "duration": "12:34",
    #     "views": 45000,
    #     "thumbnail": "https://img.youtube.com/vi/xxx/maxresdefault.jpg",
    #     "description": "Description courte",
    #     "relevance_score": 8.5
    #   }
    # ]

    suggested_lessons = models.JSONField(default=list)
    # Structure :
    # [
    #   {
    #     "title": "Introduction au plastique PET",
    #     "description": "Dans cette leçon...",
    #     "video_url": "https://youtube.com/watch?v=xxx",
    #     "key_points": ["Point 1", "Point 2"],
    #     "duration_minutes": 15,
    #     "order": 1
    #   }
    # ]

    pdf_content = models.TextField(blank=True)
    # Contenu Markdown du PDF de support généré par l'IA

    quiz_questions = models.JSONField(default=list)
    # Structure :
    # [
    #   {
    #     "question": "Quel est le taux de recyclage du PET en Haïti ?",
    #     "options": ["5%", "10%", "20%", "35%"],
    #     "correct_answer": 1,
    #     "explanation": "Explication de la bonne réponse"
    #   }
    # ]

    estimated_duration_minutes = models.PositiveIntegerField(default=0)
    tags = models.JSONField(default=list)
    category_slug = models.CharField(max_length=50, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    created_course = models.OneToOneField(
        'Course', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='recommendation'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'course_recommendations'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'
```

### Dans apps/blog/models.py — Ajouter BlogRecommendation

```python
class BlogRecommendation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('published', 'Publié'),
    ]

    suggested_title = models.CharField(max_length=300)
    seo_title = models.CharField(max_length=60, blank=True)
    angle = models.TextField()
    # L'angle éditorial suggéré par l'IA

    sources = models.JSONField(default=list)
    # Structure :
    # [
    #   {
    #     "title": "Titre de la source",
    #     "url": "https://...",
    #     "snippet": "Extrait pertinent",
    #     "source_type": "news|youtube|article"
    #   }
    # ]

    generated_content = models.TextField(blank=True)
    # Article complet généré en Markdown

    excerpt = models.TextField(blank=True, max_length=500)
    tags = models.JSONField(default=list)
    estimated_read_time = models.PositiveIntegerField(default=5)
    word_count = models.PositiveIntegerField(default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    created_post = models.OneToOneField(
        'Post', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='recommendation'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'blog_recommendations'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.suggested_title} ({self.get_status_display()})'
```

---

## PARTIE 2 — AGENT ACADEMY CURATOR

### Créer apps/agents/academy_curator.py

```python
"""
Agent Academy Curator — EcoCycle Haiti
Cherche des tutoriels YouTube pertinents sur le recyclage,
génère des cours complets structurés, et soumet à l'approbation admin.
"""

import json
import urllib.request
import urllib.parse
from anthropic import Anthropic
from django.conf import settings
from django.utils import timezone

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
      "key_points": [
        "Point clé 1",
        "Point clé 2",
        "Point clé 3"
      ],
      "duration_minutes": 15,
      "order": 1
    }
  ],
  "pdf_content": "# Titre du cours\\n\\n## Introduction\\n\\nContenu Markdown complet du document de support (500 mots min)...",
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


class AcademyCuratorAgent:

    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.youtube_api_key = getattr(settings, 'YOUTUBE_API_KEY', None)

    def search_youtube_videos(self, query: str, max_results: int = 5) -> list:
        """Recherche des vidéos YouTube via l'API."""
        if not self.youtube_api_key:
            return self._mock_videos(query)

        params = urllib.parse.urlencode({
            'part': 'snippet,contentDetails,statistics',
            'q': query,
            'type': 'video',
            'maxResults': max_results,
            'order': 'relevance',
            'videoDuration': 'medium',  # 4-20 minutes
            'relevanceLanguage': 'fr',
            'key': self.youtube_api_key,
        })

        url = f'https://www.googleapis.com/youtube/v3/search?{params}'

        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read())

            videos = []
            for item in data.get('items', []):
                snippet = item.get('snippet', {})
                video_id = item['id'].get('videoId', '')
                if not video_id:
                    continue

                # Récupérer les statistiques de la vidéo
                stats = self._get_video_stats(video_id)

                videos.append({
                    'title': snippet.get('title', ''),
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'video_id': video_id,
                    'channel': snippet.get('channelTitle', ''),
                    'thumbnail': f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
                    'description': snippet.get('description', '')[:300],
                    'published_at': snippet.get('publishedAt', ''),
                    'views': stats.get('views', 0),
                    'duration': stats.get('duration', ''),
                })

            # Filtrer : vidéos avec > 500 vues uniquement
            return [v for v in videos if v['views'] > 500]

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'YouTube API error: {e}')
            return []

    def _get_video_stats(self, video_id: str) -> dict:
        """Récupère les statistiques d'une vidéo."""
        params = urllib.parse.urlencode({
            'part': 'statistics,contentDetails',
            'id': video_id,
            'key': self.youtube_api_key,
        })
        url = f'https://www.googleapis.com/youtube/v3/videos?{params}'
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read())
            item = data['items'][0] if data.get('items') else {}
            return {
                'views': int(item.get('statistics', {}).get('viewCount', 0)),
                'duration': item.get('contentDetails', {}).get('duration', ''),
            }
        except Exception:
            return {'views': 0, 'duration': ''}

    def _mock_videos(self, query: str) -> list:
        """Données mock si pas de clé YouTube API (dev/test)."""
        return [
            {
                'title': f'Tutoriel : {query}',
                'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'video_id': 'dQw4w9WgXcQ',
                'channel': 'EcoCycle Demo',
                'thumbnail': 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
                'description': f'Tutoriel complet sur {query} adapté au contexte haïtien.',
                'views': 15000,
                'duration': 'PT12M30S',
            }
        ]

    def evaluate_and_group_videos(self, all_videos: list) -> list:
        """Demande à Claude d'évaluer et regrouper les vidéos en cours cohérents."""

        response = self.client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=2048,
            system="""Tu es un expert en éducation sur le recyclage et l'environnement.
Analyse ces vidéos YouTube et regroupe-les en 2-3 cours cohérents et pertinents
pour EcoCycle Haiti.

Pour chaque groupe, évalue la pertinence (1-10) par rapport au recyclage en Haïti.
Ne garde que les groupes avec score >= 6.

Retourne UNIQUEMENT un JSON valide :
{
  "course_groups": [
    {
      "theme": "Thème du cours",
      "relevance_score": 8.5,
      "videos": [
        {
          "url": "url_youtube",
          "title": "titre",
          "relevance_score": 9.0,
          "why_relevant": "Pourquoi cette vidéo est pertinente pour Haïti"
        }
      ]
    }
  ]
}""",
            messages=[{
                'role': 'user',
                'content': f"""Analyse et regroupe ces vidéos en cours cohérents
sur le recyclage et l'environnement pour EcoCycle Haiti :

{json.dumps(all_videos[:30], indent=2, ensure_ascii=False)}"""
            }]
        )

        raw = response.content[0].text.strip()
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        return json.loads(raw).get('course_groups', [])

    def generate_full_course(self, videos: list, theme: str) -> dict:
        """Génère un cours complet à partir d'un groupe de vidéos."""

        response = self.client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=4096,
            system=ACADEMY_CURATOR_SYSTEM_PROMPT,
            messages=[{
                'role': 'user',
                'content': f"""Crée un cours complet et structuré sur le thème :
"{theme}"

Basé sur ces vidéos YouTube :
{json.dumps(videos, indent=2, ensure_ascii=False)}

Le cours doit être adapté au contexte haïtien et inclure :
- 3 à 5 leçons bien structurées
- Un document PDF de support complet en Markdown
- 5 questions de quiz de validation
- Des exemples concrets tirés de la réalité haïtienne"""
            }]
        )

        raw = response.content[0].text.strip()
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        return json.loads(raw)

    def run(self) -> dict:
        """Exécute l'agent — recherche, évalue, génère et soumet."""
        from apps.academy.models import CourseRecommendation
        from apps.accounts.models import User
        from apps.notifications.models import Notification
        from apps.notifications.email_service import EmailService
        import random

        # 1. Rechercher des vidéos sur plusieurs requêtes
        all_videos = []
        queries = random.sample(SEARCH_QUERIES, min(4, len(SEARCH_QUERIES)))

        for query in queries:
            videos = self.search_youtube_videos(query, max_results=5)
            all_videos.extend(videos)

        if not all_videos:
            return {'status': 'no_videos_found'}

        # Dédupliquer par video_id
        seen = set()
        unique_videos = []
        for v in all_videos:
            if v['video_id'] not in seen:
                seen.add(v['video_id'])
                unique_videos.append(v)

        # 2. Claude évalue et regroupe les vidéos
        course_groups = self.evaluate_and_group_videos(unique_videos)

        if not course_groups:
            return {'status': 'no_relevant_groups'}

        # 3. Générer les cours complets (max 2 par run)
        created_recommendations = []
        for group in course_groups[:2]:
            if group['relevance_score'] < 6:
                continue

            try:
                course_data = self.generate_full_course(
                    group['videos'],
                    group['theme']
                )

                # Sauvegarder en DB comme recommandation en attente
                recommendation = CourseRecommendation.objects.create(
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
                created_recommendations.append(recommendation)

            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f'Course generation error: {e}')
                continue

        if not created_recommendations:
            return {'status': 'generation_failed'}

        # 4. Notifier les admins
        admins = User.objects.filter(role='admin', is_active=True)
        count = len(created_recommendations)

        for admin in admins:
            # Notification in-app
            Notification.objects.create(
                user=admin,
                notification_type='system',
                title=f'🎓 {count} nouveau(x) cours suggéré(s) par l\'IA',
                message=f'L\'agent Academy a trouvé {count} formation(s) '
                        f'pertinente(s) sur le recyclage. Consultez les '
                        f'recommandations pour les approuver.',
                data={
                    'type': 'academy_recommendation',
                    'count': count,
                    'recommendation_ids': [str(r.id) for r in created_recommendations],
                },
            )

            # Email détaillé
            courses_html = ''.join([
                f'<li><b>{r.title}</b> — {r.get_level_display()} — '
                f'{len(r.suggested_lessons)} leçons</li>'
                for r in created_recommendations
            ])
            EmailService._send(
                admin.email,
                f'[EcoCycle Academy] {count} nouveau(x) cours à approuver',
                f'''
                <h2>🎓 Recommandations Academy IA</h2>
                <p>L\'agent Academy Curator a généré {count} nouveau(x) cours :</p>
                <ul>{courses_html}</ul>
                <p>
                    <a href="{settings.FRONTEND_URL}/panel/recommendations/"
                       style="background:#0d7a45;color:white;padding:12px 24px;
                              border-radius:8px;text-decoration:none;">
                        Voir les recommandations →
                    </a>
                </p>
                '''
            )

        return {
            'status': 'success',
            'courses_generated': count,
            'titles': [r.title for r in created_recommendations],
        }


# Singleton
academy_curator = AcademyCuratorAgent()
```

---

## PARTIE 3 — AGENT BLOG WRITER

### Créer apps/agents/blog_writer.py

```python
"""
Agent Blog Writer — EcoCycle Haiti
Génère des suggestions d'articles sur le recyclage et l'environnement,
soumet à l'approbation admin, puis rédige l'article complet si approuvé.
"""

import json
import urllib.request
import urllib.parse
from anthropic import Anthropic
from django.conf import settings
from django.utils import timezone

BLOG_WRITER_SYSTEM_PROMPT = """
Tu es un journaliste expert en environnement et recyclage en Haïti.
Tu écris pour le blog EcoCycle Haiti — une plateforme de recyclage intelligent.

STYLE ÉDITORIAL :
- Informatif mais accessible au grand public haïtien
- Exemples concrets tirés de la réalité haïtienne
- Ton positif et encourageant (le recyclage comme opportunité)
- Données chiffrées quand disponibles
- CTA subtil vers la plateforme EcoCycle à la fin

STRUCTURE D'ARTICLE :
1. Titre SEO (50-60 caractères)
2. Introduction accrocheuse (100 mots) — chiffre ou fait surprenant
3. Section 1 — Contexte/Problème (200 mots)
4. Section 2 — Solutions/Opportunités (200 mots)
5. Section 3 — Comment agir localement (200 mots)
6. Conclusion + CTA EcoCycle (100 mots)

THÈMES PRIORITAIRES :
- Recyclage en Haïti (état des lieux, progrès, défis)
- Valorisation économique des déchets
- Impact environnemental positif du recyclage
- Portraits de recycleurs/collecteurs haïtiens
- Innovations en économie circulaire dans les Caraïbes
- Conseils pratiques de tri à la maison

RETOURNE UNIQUEMENT un JSON valide sans markdown ni backticks :
{
  "title": "Titre de l'article",
  "seo_title": "Titre SEO optimisé (60 chars max)",
  "excerpt": "Résumé de 150 mots pour la liste du blog",
  "content": "Article complet en Markdown (800-1200 mots)",
  "tags": ["recyclage", "haïti", "environnement"],
  "estimated_read_time": 5,
  "word_count": 900
}
"""

BLOG_TOPICS = [
    "recyclage plastique Haïti 2026",
    "économie circulaire Caraïbes",
    "déchets électroniques e-waste pays développement",
    "valorisation déchets emploi Haïti",
    "pollution plastique mer Caraïbes solutions",
    "startup recyclage Afrique Caraïbes",
    "impact CO2 recyclage bénéfices",
    "collecteurs déchets économie informelle",
    "compostage agriculture Haïti",
    "innovation recyclage pays émergents",
]


class BlogWriterAgent:

    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.search_api_key = getattr(settings, 'GOOGLE_SEARCH_API_KEY', None)
        self.search_engine_id = getattr(settings, 'GOOGLE_SEARCH_ENGINE_ID', None)

    def search_news(self, query: str) -> list:
        """Recherche des actualités via Google Custom Search API."""
        if not self.search_api_key or not self.search_engine_id:
            return self._mock_news(query)

        params = urllib.parse.urlencode({
            'key': self.search_api_key,
            'cx': self.search_engine_id,
            'q': query,
            'num': 5,
            'dateRestrict': 'm3',  # 3 derniers mois
            'lr': 'lang_fr',
        })

        url = f'https://www.googleapis.com/customsearch/v1?{params}'
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read())

            return [
                {
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'source_type': 'news',
                }
                for item in data.get('items', [])
            ]
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'Google Search API error: {e}')
            return []

    def _mock_news(self, query: str) -> list:
        """Mock si pas de clé Google Search (dev/test)."""
        return [
            {
                'title': f'Actualité : {query}',
                'url': 'https://example.com/article',
                'snippet': f'Les dernières nouvelles sur {query} en Haïti et dans la région.',
                'source_type': 'news',
            }
        ]

    def generate_article_suggestions(self, sources: list, topic: str) -> dict:
        """Génère des suggestions d'articles basées sur les sources trouvées."""

        response = self.client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=1024,
            system="""Tu es un éditeur de blog spécialisé en recyclage et environnement.
Analyse ces sources et propose UN angle d'article original et pertinent pour EcoCycle Haiti.

Retourne UNIQUEMENT un JSON valide :
{
  "suggested_title": "Titre suggéré",
  "angle": "L'angle éditorial et l'approche unique de cet article",
  "why_relevant": "Pourquoi ce sujet est pertinent pour EcoCycle Haiti maintenant",
  "key_points_to_cover": ["Point 1", "Point 2", "Point 3"],
  "relevance_score": 8.5
}""",
            messages=[{
                'role': 'user',
                'content': f"""Sujet : {topic}

Sources trouvées :
{json.dumps(sources, indent=2, ensure_ascii=False)}

Propose un angle original pour un article de blog EcoCycle Haiti."""
            }]
        )

        raw = response.content[0].text.strip()
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        return json.loads(raw)

    def write_full_article(self, suggestion: dict, sources: list) -> dict:
        """Rédige l'article complet basé sur la suggestion approuvée."""

        response = self.client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=3000,
            system=BLOG_WRITER_SYSTEM_PROMPT,
            messages=[{
                'role': 'user',
                'content': f"""Rédige un article complet pour le blog EcoCycle Haiti.

Titre suggéré : {suggestion['suggested_title']}
Angle : {suggestion['angle']}
Points clés à couvrir : {suggestion.get('key_points_to_cover', [])}

Sources de référence :
{json.dumps(sources, indent=2, ensure_ascii=False)}

L'article doit :
- Faire 800 à 1200 mots
- Être adapté au contexte haïtien
- Se terminer par un CTA vers EcoCycle Haiti
- Être en Markdown avec titres et sous-titres"""
            }]
        )

        raw = response.content[0].text.strip()
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        return json.loads(raw)

    def run(self) -> dict:
        """Exécute l'agent blog — recherche, suggère, et notifie."""
        from apps.blog.models import BlogRecommendation
        from apps.accounts.models import User
        from apps.notifications.models import Notification
        from apps.notifications.email_service import EmailService
        import random

        # 1. Choisir 3 sujets aléatoires
        topics = random.sample(BLOG_TOPICS, min(3, len(BLOG_TOPICS)))
        created_recommendations = []

        for topic in topics:
            try:
                # 2. Chercher des sources
                sources = self.search_news(topic)

                # 3. Générer une suggestion d'article
                suggestion = self.generate_article_suggestions(sources, topic)

                if suggestion.get('relevance_score', 0) < 6:
                    continue

                # 4. Sauvegarder la suggestion (sans rédiger l'article complet)
                # L'article complet sera généré APRÈS approbation admin
                recommendation = BlogRecommendation.objects.create(
                    suggested_title=suggestion['suggested_title'],
                    angle=suggestion['angle'],
                    sources=sources,
                    tags=['recyclage', 'environnement', 'haïti'],
                    status='pending',
                )
                created_recommendations.append(recommendation)

            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f'Blog suggestion error: {e}')
                continue

        if not created_recommendations:
            return {'status': 'no_suggestions_generated'}

        # 5. Notifier les admins
        admins = User.objects.filter(role='admin', is_active=True)
        count = len(created_recommendations)

        for admin in admins:
            Notification.objects.create(
                user=admin,
                notification_type='system',
                title=f'✍️ {count} article(s) suggéré(s) pour le blog',
                message=f'L\'agent Blog Writer a trouvé {count} sujet(s) '
                        f'd\'articles pertinents. Consultez les recommandations.',
                data={
                    'type': 'blog_recommendation',
                    'count': count,
                    'recommendation_ids': [str(r.id) for r in created_recommendations],
                },
            )

            articles_html = ''.join([
                f'<li><b>{r.suggested_title}</b></li>'
                for r in created_recommendations
            ])
            EmailService._send(
                admin.email,
                f'[EcoCycle Blog] {count} article(s) à approuver',
                f'''
                <h2>✍️ Suggestions Blog IA</h2>
                <p>L\'agent Blog Writer a généré {count} suggestion(s) d\'articles :</p>
                <ul>{articles_html}</ul>
                <p>
                    <a href="{settings.FRONTEND_URL}/panel/recommendations/"
                       style="background:#0d7a45;color:white;padding:12px 24px;
                              border-radius:8px;text-decoration:none;">
                        Voir les recommandations →
                    </a>
                </p>
                '''
            )

        return {
            'status': 'success',
            'articles_suggested': count,
            'titles': [r.suggested_title for r in created_recommendations],
        }

    def publish_approved_article(self, recommendation_id: str) -> dict:
        """
        Appelé quand un admin approuve une suggestion.
        Rédige l'article complet et le publie sur le blog.
        """
        from apps.blog.models import BlogRecommendation, Post, BlogCategory
        from apps.accounts.models import User
        from django.utils.text import slugify

        recommendation = BlogRecommendation.objects.get(id=recommendation_id)

        # Rédiger l'article complet
        article_data = self.write_full_article(
            {
                'suggested_title': recommendation.suggested_title,
                'angle': recommendation.angle,
            },
            recommendation.sources,
        )

        # Trouver ou créer la catégorie "Environnement"
        category, _ = BlogCategory.objects.get_or_create(
            slug='environnement',
            defaults={'name': 'Environnement'},
        )

        # Trouver l'auteur admin (agent IA)
        admin = User.objects.filter(role='admin', is_active=True).first()

        # Créer le slug unique
        base_slug = slugify(article_data.get('seo_title', recommendation.suggested_title))
        slug = base_slug
        counter = 1
        while Post.objects.filter(slug=slug).exists():
            slug = f'{base_slug}-{counter}'
            counter += 1

        # Créer et publier le post
        post = Post.objects.create(
            author=admin,
            category=category,
            title=article_data.get('title', recommendation.suggested_title),
            slug=slug,
            excerpt=article_data.get('excerpt', '')[:500],
            content=article_data.get('content', ''),
            status='published',
            read_time_minutes=article_data.get('estimated_read_time', 5),
            published_at=timezone.now(),
        )

        # Mettre à jour la recommandation
        recommendation.generated_content = article_data.get('content', '')
        recommendation.excerpt = article_data.get('excerpt', '')
        recommendation.word_count = article_data.get('word_count', 0)
        recommendation.estimated_read_time = article_data.get('estimated_read_time', 5)
        recommendation.status = 'published'
        recommendation.created_post = post
        recommendation.published_at = timezone.now()
        recommendation.save()

        return {
            'status': 'published',
            'post_id': str(post.id),
            'post_slug': post.slug,
            'title': post.title,
        }


# Singleton
blog_writer = BlogWriterAgent()
```

---

## PARTIE 4 — TÂCHES CELERY

### Mettre à jour apps/agents/tasks.py

```python
# Ajouter ces tâches aux tâches existantes

@shared_task(name='agents.run_academy_curator')
def run_academy_curator():
    """Cherche et génère des cours toutes les 2 semaines."""
    from .academy_curator import academy_curator
    try:
        result = academy_curator.run()
        logger.info(f'Academy Curator: {result}')
        return result
    except Exception as e:
        logger.error(f'Academy Curator error: {e}')
        raise


@shared_task(name='agents.run_blog_writer')
def run_blog_writer():
    """Génère des suggestions d'articles chaque semaine."""
    from .blog_writer import blog_writer
    try:
        result = blog_writer.run()
        logger.info(f'Blog Writer: {result}')
        return result
    except Exception as e:
        logger.error(f'Blog Writer error: {e}')
        raise


@shared_task(name='agents.publish_approved_course')
def publish_approved_course(recommendation_id: str):
    """
    Appelé quand un admin approuve un cours.
    Crée le cours complet en DB avec toutes ses leçons.
    """
    from .academy_curator import academy_curator
    from apps.academy.models import CourseRecommendation, Course, Lesson
    from django.utils import timezone

    recommendation = CourseRecommendation.objects.get(id=recommendation_id)

    # Créer le cours
    course = Course.objects.create(
        title=recommendation.title,
        description=recommendation.description,
        level=recommendation.level,
        duration_minutes=recommendation.estimated_duration_minutes,
        is_published=True,
        is_free=True,
    )

    # Créer les leçons
    for lesson_data in recommendation.suggested_lessons:
        Lesson.objects.create(
            course=course,
            title=lesson_data.get('title', ''),
            content=lesson_data.get('description', ''),
            video_url=lesson_data.get('video_url', ''),
            order=lesson_data.get('order', 1),
            duration_minutes=lesson_data.get('duration_minutes', 15),
        )

    # Mettre à jour la recommandation
    recommendation.status = 'published'
    recommendation.created_course = course
    recommendation.published_at = timezone.now()
    recommendation.save()

    # Notifier les admins
    from apps.accounts.models import User
    from apps.notifications.models import Notification
    admins = User.objects.filter(role='admin', is_active=True)
    for admin in admins:
        Notification.objects.create(
            user=admin,
            notification_type='system',
            title=f'✅ Cours publié : {course.title}',
            message=f'Le cours "{course.title}" avec {course.lessons.count()} '
                    f'leçons est maintenant en ligne sur l\'Academy.',
            data={'course_id': str(course.id)},
        )

    return {
        'status': 'published',
        'course_id': str(course.id),
        'lessons_count': course.lessons.count(),
    }


@shared_task(name='agents.publish_approved_article')
def publish_approved_article(recommendation_id: str):
    """
    Appelé quand un admin approuve un article.
    Rédige et publie l'article complet.
    """
    from .blog_writer import blog_writer
    try:
        result = blog_writer.publish_approved_article(recommendation_id)
        logger.info(f'Article published: {result}')
        return result
    except Exception as e:
        logger.error(f'Article publish error: {e}')
        raise
```

---

## PARTIE 5 — PLANIFICATION CELERY BEAT

### Dans config/celery.py — Ajouter dans beat_schedule

```python
from celery.schedules import crontab

# Ajouter ces entrées dans beat_schedule :

'run-academy-curator': {
    'task': 'agents.run_academy_curator',
    'schedule': crontab(hour=9, minute=0, day_of_week=1),
    # Chaque lundi matin à 9h (heure Haïti)
},
'run-blog-writer': {
    'task': 'agents.run_blog_writer',
    'schedule': crontab(hour=8, minute=30, day_of_week=3),
    # Chaque mercredi matin à 8h30 (heure Haïti)
},
```

---

## PARTIE 6 — VUES ADMIN (panel de recommandations)

### Dans web/views/admin_views.py — Ajouter ces vues

```python
from apps.academy.models import CourseRecommendation
from apps.blog.models import BlogRecommendation
from apps.agents.tasks import publish_approved_course, publish_approved_article


class AdminRecommendationsView(AdminRequiredMixin, View):
    """
    GET /panel/recommendations/
    Page principale des recommandations IA en attente.
    """
    def get(self, request):
        course_recs = CourseRecommendation.objects.filter(
            status='pending'
        ).order_by('-created_at')

        blog_recs = BlogRecommendation.objects.filter(
            status='pending'
        ).order_by('-created_at')

        published_courses = CourseRecommendation.objects.filter(
            status='published'
        ).order_by('-published_at')[:5]

        published_articles = BlogRecommendation.objects.filter(
            status='published'
        ).order_by('-published_at')[:5]

        return render(request, 'admin_panel/recommendations.html', {
            'course_recommendations': course_recs,
            'blog_recommendations': blog_recs,
            'published_courses': published_courses,
            'published_articles': published_articles,
            'pending_count': course_recs.count() + blog_recs.count(),
        })


class AdminApproveCourseView(AdminRequiredMixin, View):
    """POST /panel/recommendations/course/<id>/approve/"""
    def post(self, request, pk):
        recommendation = get_object_or_404(CourseRecommendation, pk=pk)
        recommendation.status = 'approved'
        recommendation.reviewed_at = timezone.now()
        recommendation.save()

        # Lancer la publication en arrière-plan
        publish_approved_course.delay(str(recommendation.id))

        messages.success(
            request,
            f'Cours "{recommendation.title}" approuvé ! '
            f'Il sera publié dans quelques secondes.'
        )
        return redirect('admin_recommendations')


class AdminRejectCourseView(AdminRequiredMixin, View):
    """POST /panel/recommendations/course/<id>/reject/"""
    def post(self, request, pk):
        recommendation = get_object_or_404(CourseRecommendation, pk=pk)
        recommendation.status = 'rejected'
        recommendation.rejection_reason = request.POST.get('reason', '')
        recommendation.reviewed_at = timezone.now()
        recommendation.save()
        messages.warning(request, f'Cours "{recommendation.title}" rejeté.')
        return redirect('admin_recommendations')


class AdminApproveBlogView(AdminRequiredMixin, View):
    """POST /panel/recommendations/blog/<id>/approve/"""
    def post(self, request, pk):
        recommendation = get_object_or_404(BlogRecommendation, pk=pk)
        recommendation.status = 'approved'
        recommendation.reviewed_at = timezone.now()
        recommendation.save()

        # Lancer la rédaction + publication en arrière-plan
        publish_approved_article.delay(str(recommendation.id))

        messages.success(
            request,
            f'Article "{recommendation.suggested_title}" approuvé ! '
            f'L\'IA va rédiger et publier l\'article.'
        )
        return redirect('admin_recommendations')


class AdminRejectBlogView(AdminRequiredMixin, View):
    """POST /panel/recommendations/blog/<id>/reject/"""
    def post(self, request, pk):
        recommendation = get_object_or_404(BlogRecommendation, pk=pk)
        recommendation.status = 'rejected'
        recommendation.rejection_reason = request.POST.get('reason', '')
        recommendation.reviewed_at = timezone.now()
        recommendation.save()
        messages.warning(request, f'Article "{recommendation.suggested_title}" rejeté.')
        return redirect('admin_recommendations')


class AdminCourseRecommendationDetailView(AdminRequiredMixin, View):
    """GET /panel/recommendations/course/<id>/"""
    def get(self, request, pk):
        recommendation = get_object_or_404(CourseRecommendation, pk=pk)
        return render(request, 'admin_panel/recommendation_course_detail.html', {
            'rec': recommendation,
        })


class AdminBlogRecommendationDetailView(AdminRequiredMixin, View):
    """GET /panel/recommendations/blog/<id>/"""
    def get(self, request, pk):
        recommendation = get_object_or_404(BlogRecommendation, pk=pk)
        return render(request, 'admin_panel/recommendation_blog_detail.html', {
            'rec': recommendation,
        })
```

---

## PARTIE 7 — URLS

### Dans web/urls.py — Ajouter

```python
from .views.admin_views import (
    AdminRecommendationsView,
    AdminApproveCourseView, AdminRejectCourseView,
    AdminApproveBlogView, AdminRejectBlogView,
    AdminCourseRecommendationDetailView,
    AdminBlogRecommendationDetailView,
)

urlpatterns += [
    path('panel/recommendations/',
         AdminRecommendationsView.as_view(),
         name='admin_recommendations'),

    path('panel/recommendations/course/<uuid:pk>/',
         AdminCourseRecommendationDetailView.as_view(),
         name='admin_course_recommendation_detail'),

    path('panel/recommendations/course/<uuid:pk>/approve/',
         AdminApproveCourseView.as_view(),
         name='admin_approve_course'),

    path('panel/recommendations/course/<uuid:pk>/reject/',
         AdminRejectCourseView.as_view(),
         name='admin_reject_course'),

    path('panel/recommendations/blog/<uuid:pk>/',
         AdminBlogRecommendationDetailView.as_view(),
         name='admin_blog_recommendation_detail'),

    path('panel/recommendations/blog/<uuid:pk>/approve/',
         AdminApproveBlogView.as_view(),
         name='admin_approve_blog'),

    path('panel/recommendations/blog/<uuid:pk>/reject/',
         AdminRejectBlogView.as_view(),
         name='admin_reject_blog'),
]
```

---

## PARTIE 8 — TEMPLATE

### Créer templates/admin_panel/recommendations.html

```html
{% extends 'admin_panel/base_admin.html' %}
{% block admin_content %}

<div class="recommendations-page">
  <div class="page-header">
    <h1>🤖 Recommandations IA</h1>
    {% if pending_count > 0 %}
      <span class="badge-count">{{ pending_count }} en attente</span>
    {% endif %}
  </div>

  <!-- ACADEMY -->
  <section class="rec-section">
    <h2>🎓 Academy — Cours suggérés
      ({{ course_recommendations.count }})</h2>

    {% for rec in course_recommendations %}
    <div class="rec-card">
      <div class="rec-header">
        <div>
          <h3>{{ rec.title }}</h3>
          <span class="level-badge level-{{ rec.level }}">
            {{ rec.get_level_display }}
          </span>
          <span class="meta">
            {{ rec.suggested_lessons|length }} leçons ·
            {{ rec.estimated_duration_minutes }} min
          </span>
        </div>
        <div class="rec-actions">
          <a href="{% url 'admin_course_recommendation_detail' rec.id %}"
             class="btn btn-outline btn-sm">
            👁 Voir le détail
          </a>
          <form method="POST"
                action="{% url 'admin_approve_course' rec.id %}"
                style="display:inline">
            {% csrf_token %}
            <button type="submit" class="btn btn-success btn-sm">
              ✓ Approuver
            </button>
          </form>
          <button class="btn btn-danger btn-sm"
                  onclick="showRejectModal('course', '{{ rec.id }}')">
            ✗ Rejeter
          </button>
        </div>
      </div>

      <p class="rec-description">{{ rec.description|truncatewords:30 }}</p>

      <!-- Preview des vidéos YouTube -->
      <div class="videos-preview">
        {% for video in rec.youtube_videos|slice:":3" %}
        <div class="video-thumb">
          <img src="{{ video.thumbnail }}" alt="{{ video.title }}">
          <div class="video-info">
            <p class="video-title">{{ video.title|truncatechars:60 }}</p>
            <p class="video-meta">
              {{ video.channel }} · {{ video.views|floatformat:0 }} vues
            </p>
            <a href="{{ video.url }}" target="_blank"
               class="btn btn-ghost btn-xs">
              ▶ Voir sur YouTube
            </a>
          </div>
        </div>
        {% endfor %}
      </div>

      <p class="rec-date">
        Généré le {{ rec.created_at|date:"d/m/Y à H:i" }}
      </p>
    </div>
    {% empty %}
    <div class="empty-state">
      <p>🎓 Aucun cours en attente d'approbation.</p>
      <p class="text-muted">
        Le prochain scan est prévu lundi matin à 9h.
      </p>
    </div>
    {% endfor %}
  </section>

  <!-- BLOG -->
  <section class="rec-section">
    <h2>✍️ Blog — Articles suggérés
      ({{ blog_recommendations.count }})</h2>

    {% for rec in blog_recommendations %}
    <div class="rec-card">
      <div class="rec-header">
        <div>
          <h3>{{ rec.suggested_title }}</h3>
          <p class="angle-text">{{ rec.angle|truncatewords:20 }}</p>
        </div>
        <div class="rec-actions">
          <a href="{% url 'admin_blog_recommendation_detail' rec.id %}"
             class="btn btn-outline btn-sm">
            👁 Voir l'angle
          </a>
          <form method="POST"
                action="{% url 'admin_approve_blog' rec.id %}"
                style="display:inline">
            {% csrf_token %}
            <button type="submit" class="btn btn-success btn-sm">
              ✓ Approuver
            </button>
          </form>
          <button class="btn btn-danger btn-sm"
                  onclick="showRejectModal('blog', '{{ rec.id }}')">
            ✗ Rejeter
          </button>
        </div>
      </div>
      <p class="rec-date">
        Généré le {{ rec.created_at|date:"d/m/Y à H:i" }}
      </p>
    </div>
    {% empty %}
    <div class="empty-state">
      <p>✍️ Aucun article en attente d'approbation.</p>
      <p class="text-muted">
        Le prochain scan est prévu mercredi matin à 8h30.
      </p>
    </div>
    {% endfor %}
  </section>

  <!-- PUBLIÉS RÉCEMMENT -->
  {% if published_courses or published_articles %}
  <section class="rec-section published-section">
    <h2>✅ Publiés récemment</h2>
    {% for rec in published_courses %}
    <div class="published-item">
      🎓 <b>{{ rec.title }}</b>
      — publié le {{ rec.published_at|date:"d/m/Y" }}
    </div>
    {% endfor %}
    {% for rec in published_articles %}
    <div class="published-item">
      ✍️ <b>{{ rec.suggested_title }}</b>
      — publié le {{ rec.published_at|date:"d/m/Y" }}
    </div>
    {% endfor %}
  </section>
  {% endif %}
</div>

<!-- Modal de rejet -->
<div id="reject-modal" class="modal" style="display:none">
  <div class="modal-content">
    <h3>Raison du rejet</h3>
    <form id="reject-form" method="POST">
      {% csrf_token %}
      <textarea name="reason" placeholder="Expliquez pourquoi..." rows="3"
                class="form-control"></textarea>
      <div class="modal-actions">
        <button type="submit" class="btn btn-danger">Rejeter</button>
        <button type="button" class="btn btn-ghost"
                onclick="closeModal()">Annuler</button>
      </div>
    </form>
  </div>
</div>

<script>
function showRejectModal(type, id) {
  const modal = document.getElementById('reject-modal');
  const form = document.getElementById('reject-form');
  const baseUrl = type === 'course'
    ? '/panel/recommendations/course/'
    : '/panel/recommendations/blog/';
  form.action = baseUrl + id + '/reject/';
  modal.style.display = 'flex';
}
function closeModal() {
  document.getElementById('reject-modal').style.display = 'none';
}
</script>

{% endblock %}
```

---

## PARTIE 9 — VARIABLES D'ENVIRONNEMENT À AJOUTER

```bash
# Dans .env et sur Railway

# YouTube Data API v3
# Obtenir sur : console.cloud.google.com → APIs & Services → YouTube Data API v3
YOUTUBE_API_KEY=AIzaSy...

# Google Custom Search API (optionnel — pour le blog)
# Obtenir sur : console.cloud.google.com → Custom Search API
# Créer un moteur sur : programmablesearchengine.google.com
GOOGLE_SEARCH_API_KEY=AIzaSy...
GOOGLE_SEARCH_ENGINE_ID=xxx:yyy
```

---

## PARTIE 10 — MIGRATIONS

```bash
python manage.py makemigrations academy
python manage.py makemigrations blog
python manage.py migrate
```

---

## PARTIE 11 — TEST MANUEL

```bash
python manage.py shell

# Tester Academy Curator
from apps.agents.tasks import run_academy_curator
result = run_academy_curator()
print(result)

# Tester Blog Writer
from apps.agents.tasks import run_blog_writer
result = run_blog_writer()
print(result)

# Vérifier les recommandations créées
from apps.academy.models import CourseRecommendation
print(CourseRecommendation.objects.count())

from apps.blog.models import BlogRecommendation
print(BlogRecommendation.objects.count())

# Tester l'approbation manuelle d'un cours
from apps.agents.tasks import publish_approved_course
rec = CourseRecommendation.objects.first()
publish_approved_course(str(rec.id))
```

---

## RÉSUMÉ DES FICHIERS À CRÉER/MODIFIER

```
CRÉER :
apps/agents/academy_curator.py
apps/agents/blog_writer.py
templates/admin_panel/recommendations.html
templates/admin_panel/recommendation_course_detail.html
templates/admin_panel/recommendation_blog_detail.html

MODIFIER :
apps/agents/tasks.py          ← ajouter 4 nouvelles tâches
apps/academy/models.py        ← ajouter CourseRecommendation
apps/blog/models.py           ← ajouter BlogRecommendation
config/celery.py              ← ajouter 2 entrées beat_schedule
web/views/admin_views.py      ← ajouter 6 nouvelles vues
web/urls.py                   ← ajouter 7 nouvelles routes
config/settings/base.py       ← ajouter YOUTUBE_API_KEY, GOOGLE_SEARCH_API_KEY
```

---

*Agent Academy Curator & Blog Writer — EcoCycle Haiti — 2026*
