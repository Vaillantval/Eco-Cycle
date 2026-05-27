import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name='waste.analyze_photo', bind=True, max_retries=3)
def analyze_waste_photo_async(self, listing_id: str, image_b64: str = None, media_type: str = 'image/jpeg'):
    from .models import WasteListing, WasteCategory
    from .ai_service import ai_service
    from django.conf import settings

    logger.warning('analyze_photo START listing=%s b64=%s', listing_id, bool(image_b64))
    try:
        listing = WasteListing.objects.get(id=listing_id)

        if image_b64:
            # Base64 passed directly from the web pod — best path
            result = ai_service.analyze_image_from_base64(image_b64, media_type)
            logger.warning('analyze_photo used BASE64 listing=%s', listing_id)
        elif listing.photo:
            # Fallback: try local file, then public URL
            try:
                result = ai_service.analyze_image_from_file(listing.photo.path)
                logger.warning('analyze_photo used FILE listing=%s', listing_id)
            except (FileNotFoundError, OSError):
                base_url = settings.FRONTEND_URL.split(',')[0].strip().rstrip('/')
                full_url = base_url + listing.photo.url
                logger.warning('analyze_photo fallback URL=%s', full_url)
                result = ai_service.analyze_image_from_url(full_url)
        else:
            logger.warning('analyze_photo SKIP listing=%s (no photo, no b64)', listing_id)
            return

        if 'error' not in result:
            listing.ai_analysis = result
            listing.ai_estimated_value = result.get('estimated_value_htg')
            listing.ai_analyzed_at = timezone.now()
            if not listing.category and result.get('category_slug'):
                category = WasteCategory.objects.filter(slug=result['category_slug']).first()
                if category:
                    listing.category = category
            listing.save()
            logger.warning('analyze_photo SAVED listing=%s htg=%s category=%s',
                           listing_id, listing.ai_estimated_value, listing.category)
        else:
            logger.error('analyze_photo ERROR listing=%s result=%s', listing_id, result)

    except WasteListing.DoesNotExist:
        logger.error('analyze_photo NOT FOUND listing=%s', listing_id)
    except Exception as exc:
        logger.error('analyze_photo EXCEPTION listing=%s exc=%s', listing_id, repr(exc), exc_info=True)
        raise self.retry(exc=exc, countdown=60)


@shared_task(name='waste.notify_admin_new_listing')
def notify_admin_new_listing(listing_id: str):
    from .models import WasteListing
    from apps.notifications.email_service import EmailService
    from apps.notifications.fcm_service import FCMService
    from apps.accounts.models import User
    try:
        listing = WasteListing.objects.select_related('user', 'category').get(id=listing_id)
        admins = list(User.objects.filter(role='admin', is_active=True))
        for admin in admins:
            EmailService.send_admin_new_listing(admin=admin, listing=listing)
        FCMService.send_to_multiple(
            admins,
            'Nouveau listing à réviser',
            f'{listing.user.full_name} — « {listing.title} »',
            {'type': 'admin_new_listing', 'listing_id': str(listing.id)},
        )
    except WasteListing.DoesNotExist:
        pass
