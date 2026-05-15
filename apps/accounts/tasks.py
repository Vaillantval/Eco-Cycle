from celery import shared_task
from django.conf import settings
from .models import User, EmailVerificationToken, PasswordResetToken


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
