import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='agents.run_price_optimizer')
def run_price_optimizer():
    """Optimise les prix des catégories chaque nuit à minuit."""
    from .price_optimizer import price_optimizer
    try:
        result = price_optimizer.run()
        logger.warning('Price optimizer: %s', result)
        return result
    except Exception as exc:
        logger.error('Price optimizer error: %s', repr(exc), exc_info=True)
        raise


@shared_task(name='agents.run_fraud_detector')
def run_fraud_detector():
    """Scan anti-fraude toutes les heures."""
    from .fraud_detector import fraud_detector
    try:
        result = fraud_detector.run()
        logger.warning('Fraud detector: %s', result)
        return result
    except Exception as exc:
        logger.error('Fraud detector error: %s', repr(exc), exc_info=True)
        raise


@shared_task(name='agents.run_academy_curator')
def run_academy_curator():
    """Cherche et génère des cours chaque lundi matin."""
    from .academy_curator import academy_curator
    try:
        result = academy_curator.run()
        logger.warning('Academy Curator: %s', result)
        return result
    except Exception as exc:
        logger.error('Academy Curator error: %s', repr(exc), exc_info=True)
        raise


@shared_task(name='agents.run_blog_writer')
def run_blog_writer():
    """Génère des suggestions d'articles chaque mercredi matin."""
    from .blog_writer import blog_writer
    try:
        result = blog_writer.run()
        logger.warning('Blog Writer: %s', result)
        return result
    except Exception as exc:
        logger.error('Blog Writer error: %s', repr(exc), exc_info=True)
        raise


@shared_task(name='agents.publish_approved_course')
def publish_approved_course(recommendation_id: int):
    """Crée le cours complet quand un admin approuve une recommandation."""
    from apps.academy.models import CourseRecommendation, Course, Lesson, LessonVideo
    from apps.accounts.models import User
    from apps.notifications.models import Notification
    from django.utils import timezone

    try:
        recommendation = CourseRecommendation.objects.get(id=recommendation_id)

        # Générer un slug unique tronqué à 200 chars
        from django.utils.text import slugify
        base_slug = slugify(recommendation.title)[:200]
        slug = base_slug
        counter = 1
        while Course.objects.filter(slug=slug).exists():
            slug = f'{base_slug[:196]}-{counter}'
            counter += 1

        course = Course.objects.create(
            title=recommendation.title,
            slug=slug,
            description=recommendation.description,
            level=recommendation.level,
            duration_minutes=recommendation.estimated_duration_minutes,
            is_published=True,
            price=0,
        )

        for lesson_data in recommendation.suggested_lessons:
            lesson = Lesson.objects.create(
                course=course,
                title=lesson_data.get('title', ''),
                content=lesson_data.get('description', ''),
                order=lesson_data.get('order', 1),
                duration_minutes=lesson_data.get('duration_minutes', 15),
            )
            if lesson_data.get('video_url'):
                LessonVideo.objects.create(
                    lesson=lesson,
                    title=lesson_data.get('title', ''),
                    video_url=lesson_data['video_url'],
                    order=1,
                    duration_minutes=lesson_data.get('duration_minutes', 15),
                )

        recommendation.status = 'published'
        recommendation.created_course = course
        recommendation.published_at = timezone.now()
        recommendation.save()

        admins = User.objects.filter(role='admin', is_active=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                notification_type='system',
                title=f'✅ Cours publié : {course.title}',
                message=(
                    f'Le cours "{course.title}" avec {course.lessons.count()} '
                    f'leçons est maintenant en ligne sur l\'Academy.'
                ),
                data={'course_id': str(course.id)},
            )

        result = {
            'status': 'published',
            'course_id': str(course.id),
            'lessons_count': course.lessons.count(),
        }
        logger.warning('publish_approved_course: %s', result)
        return result

    except Exception as exc:
        logger.error('publish_approved_course error: %s', repr(exc), exc_info=True)
        raise


@shared_task(name='agents.publish_approved_article')
def publish_approved_article(recommendation_id: int):
    """Rédige et publie l'article complet quand un admin approuve une suggestion."""
    from .blog_writer import blog_writer
    try:
        result = blog_writer.publish_approved_article(recommendation_id)
        logger.warning('publish_approved_article: %s', result)
        return result
    except Exception as exc:
        logger.error('publish_approved_article error: %s', repr(exc), exc_info=True)
        raise
