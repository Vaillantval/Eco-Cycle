from celery import shared_task
from django.utils import timezone


@shared_task(name='waste.analyze_photo', bind=True, max_retries=3)
def analyze_waste_photo_async(self, listing_id: str):
    from .models import WasteListing, WasteCategory
    from .ai_service import ai_service
    try:
        listing = WasteListing.objects.get(id=listing_id)
        if listing.photo:
            result = ai_service.analyze_image_from_file(listing.photo.path)
            if 'error' not in result:
                listing.ai_analysis = result
                listing.ai_estimated_value = result.get('estimated_value_htg')
                listing.ai_analyzed_at = timezone.now()
                if not listing.category and result.get('category_slug'):
                    category = WasteCategory.objects.filter(slug=result['category_slug']).first()
                    if category:
                        listing.category = category
                listing.save()
    except WasteListing.DoesNotExist:
        pass
    except Exception as exc:
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
