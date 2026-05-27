import json
import logging
import urllib.request
import urllib.parse
from anthropic import Anthropic
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

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


def _strip_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith('```'):
        raw = raw.split('```')[1]
        if raw.startswith('json'):
            raw = raw[4:]
    return raw.strip()


class BlogWriterAgent:

    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.search_api_key = getattr(settings, 'GOOGLE_SEARCH_API_KEY', None)
        self.search_engine_id = getattr(settings, 'GOOGLE_SEARCH_ENGINE_ID', None)

    def search_news(self, query: str) -> list:
        if not self.search_api_key or not self.search_engine_id:
            return self._mock_news(query)

        params = urllib.parse.urlencode({
            'key': self.search_api_key,
            'cx': self.search_engine_id,
            'q': query,
            'num': 5,
            'dateRestrict': 'm3',
            'lr': 'lang_fr',
        })
        url = f'https://www.googleapis.com/customsearch/v1?{params}'
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
            return [
                {
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'source_type': 'news',
                }
                for item in data.get('items', [])
            ]
        except Exception as exc:
            logger.error('Google Search API error: %s', exc)
            return []

    def _mock_news(self, query: str) -> list:
        return [{
            'title': f'Actualité : {query}',
            'url': 'https://example.com/article',
            'snippet': f'Les dernières nouvelles sur {query} en Haïti et dans la région.',
            'source_type': 'news',
        }]

    def generate_article_suggestion(self, sources: list, topic: str) -> dict:
        response = self.client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=1024,
            system="""Tu es un éditeur de blog spécialisé en recyclage et environnement.
Analyse ces sources et propose UN angle d'article original pour EcoCycle Haiti.
Retourne UNIQUEMENT un JSON valide :
{
  "suggested_title": "Titre suggéré",
  "angle": "L'angle éditorial et l'approche unique",
  "why_relevant": "Pourquoi ce sujet est pertinent pour EcoCycle Haiti maintenant",
  "key_points_to_cover": ["Point 1", "Point 2", "Point 3"],
  "relevance_score": 8.5
}""",
            messages=[{
                'role': 'user',
                'content': (
                    f'Sujet : {topic}\n\nSources :\n'
                    f'{json.dumps(sources, indent=2, ensure_ascii=False)}\n\n'
                    f'Propose un angle original pour un article de blog EcoCycle Haiti.'
                ),
            }],
        )
        try:
            return json.loads(_strip_json(response.content[0].text))
        except Exception as exc:
            logger.error('generate_article_suggestion parse error: %s', exc)
            raise

    def write_full_article(self, suggestion: dict, sources: list) -> dict:
        response = self.client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=3000,
            system=BLOG_WRITER_SYSTEM_PROMPT,
            messages=[{
                'role': 'user',
                'content': (
                    f'Rédige un article complet pour le blog EcoCycle Haiti.\n\n'
                    f'Titre suggéré : {suggestion["suggested_title"]}\n'
                    f'Angle : {suggestion["angle"]}\n'
                    f'Points clés : {suggestion.get("key_points_to_cover", [])}\n\n'
                    f'Sources de référence :\n'
                    f'{json.dumps(sources, indent=2, ensure_ascii=False)}\n\n'
                    f'L\'article doit faire 800-1200 mots, être en Markdown, '
                    f'et se terminer par un CTA vers EcoCycle Haiti.'
                ),
            }],
        )
        try:
            return json.loads(_strip_json(response.content[0].text))
        except Exception as exc:
            logger.error('write_full_article parse error: %s', exc)
            raise

    def run(self) -> dict:
        from apps.blog.models import BlogRecommendation
        from apps.accounts.models import User
        from apps.notifications.models import Notification
        from apps.notifications.email_service import EmailService
        import random

        topics = random.sample(BLOG_TOPICS, min(3, len(BLOG_TOPICS)))
        created = []

        for topic in topics:
            try:
                sources = self.search_news(topic)
                suggestion = self.generate_article_suggestion(sources, topic)
                if suggestion.get('relevance_score', 0) < 6:
                    continue
                rec = BlogRecommendation.objects.create(
                    suggested_title=suggestion['suggested_title'],
                    angle=suggestion['angle'],
                    sources=sources,
                    tags=['recyclage', 'environnement', 'haïti'],
                    status='pending',
                )
                created.append(rec)
            except Exception as exc:
                logger.error('Blog suggestion error for topic "%s": %s', topic, exc)

        if not created:
            return {'status': 'no_suggestions_generated'}

        count = len(created)
        admins = User.objects.filter(role='admin', is_active=True)
        articles_html = ''.join(f'<li><b>{r.suggested_title}</b></li>' for r in created)
        frontend_url = settings.FRONTEND_URL.split(',')[0].strip().rstrip('/')

        for admin in admins:
            Notification.objects.create(
                user=admin,
                notification_type='system',
                title=f'✍️ {count} article(s) suggéré(s) pour le blog',
                message=(
                    f'L\'agent Blog Writer a trouvé {count} sujet(s) d\'articles pertinents. '
                    f'Consultez les recommandations.'
                ),
                data={
                    'type': 'blog_recommendation',
                    'count': count,
                    'recommendation_ids': [str(r.id) for r in created],
                },
            )
            EmailService._send(
                admin.email,
                f'[EcoCycle Blog] {count} article(s) à approuver',
                f'''<h2>✍️ Suggestions Blog IA</h2>
                <p>L\'agent Blog Writer a généré {count} suggestion(s) d\'articles :</p>
                <ul>{articles_html}</ul>
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
            'articles_suggested': count,
            'titles': [r.suggested_title for r in created],
        }

    def publish_approved_article(self, recommendation_id: int) -> dict:
        from apps.blog.models import BlogRecommendation, BlogCategory, Post
        from apps.accounts.models import User
        from django.utils.text import slugify

        recommendation = BlogRecommendation.objects.get(id=recommendation_id)
        article_data = self.write_full_article(
            {
                'suggested_title': recommendation.suggested_title,
                'angle': recommendation.angle,
            },
            recommendation.sources,
        )

        category, _ = BlogCategory.objects.get_or_create(
            slug='environnement',
            defaults={'name': 'Environnement'},
        )
        admin = User.objects.filter(role='admin', is_active=True).first()

        base_slug = slugify(article_data.get('seo_title', recommendation.suggested_title))
        slug = base_slug
        counter = 1
        while Post.objects.filter(slug=slug).exists():
            slug = f'{base_slug}-{counter}'
            counter += 1

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


blog_writer = BlogWriterAgent()
