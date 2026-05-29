import logging
from celery import shared_task
from django.conf import settings
from .models import User, EmailVerificationToken, PasswordResetToken

logger = logging.getLogger(__name__)


@shared_task(name='accounts.send_verification_email')
def send_verification_email(user_id: str):
    from apps.notifications.email_service import EmailService
    try:
        user = User.objects.get(id=user_id)
        token, _ = EmailVerificationToken.objects.get_or_create(user=user)
        verify_url = f"{settings.FRONTEND_URL}/verify-email/{token.token}"
        EmailService.send_welcome(user=user, verify_url=verify_url)
    except User.DoesNotExist:
        pass
    except Exception:
        pass


@shared_task(name='accounts.send_password_reset_email')
def send_password_reset_email(user_id: str):
    from apps.notifications.email_service import EmailService
    try:
        user = User.objects.get(id=user_id)
        token = PasswordResetToken.objects.create(user=user)
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{token.token}"
        EmailService.send_password_reset(user=user, reset_url=reset_url)
    except User.DoesNotExist:
        pass
    except Exception:
        pass


@shared_task(name='accounts.geocode_user_location')
def geocode_user_location(user_id: str):
    """Géocode l'adresse de l'utilisateur et met à jour latitude/longitude."""
    from .geocoding_service import geocode_address
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return
    if not (user.address or user.city):
        return
    result = geocode_address(user.address, user.city)
    if result:
        lat, lon = result
        User.objects.filter(pk=user.pk).update(latitude=lat, longitude=lon)
        logger.info('Geocoded user %s → (%s, %s)', user.email, lat, lon)
    else:
        logger.warning('Geocoding failed for user %s (%s, %s)', user.email, user.address, user.city)
