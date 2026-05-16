from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(name='core.notify_maintenance_over', bind=True, max_retries=3)
def notify_maintenance_over(self, message: str = ''):
    """
    Notifie tous les utilisateurs actifs que la maintenance est terminée :
    - Email via Resend (par lots de 50)
    - Push FCM multicast (un seul appel pour tous les tokens)
    """
    from apps.accounts.models import User
    from apps.notifications.email_service import EmailService
    from apps.notifications.fcm_service import FCMService

    users = list(User.objects.filter(is_active=True).only(
        'email', 'first_name', 'fcm_token'
    ))

    if not users:
        return 'Aucun utilisateur actif.'

    # ── Push FCM (multicast) ──────────────────────────────────────────────────
    try:
        FCMService.send_to_multiple(
            users,
            title='EcoCycle est de retour ! 🎉',
            body=message or 'Le site est à nouveau disponible. Merci pour votre patience.',
            data={'type': 'maintenance_over'},
        )
        logger.info(f'FCM multicast envoyé à {len(users)} utilisateurs.')
    except Exception as e:
        logger.error(f'FCM multicast erreur : {e}')

    # ── Emails par lots de 50 ────────────────────────────────────────────────
    sent = 0
    errors = 0
    chunk_size = 50
    for i in range(0, len(users), chunk_size):
        chunk = users[i:i + chunk_size]
        for user in chunk:
            try:
                EmailService.send_maintenance_over(user, message=message)
                sent += 1
            except Exception as e:
                logger.error(f'Email maintenance_over erreur ({user.email}): {e}')
                errors += 1

    return f'Emails : {sent} envoyés, {errors} erreurs.'


@shared_task(name='core.send_weekly_report')
def send_weekly_report():
    from django.db.models import Sum, Count
    from apps.accounts.models import User
    from apps.marketplace.models import Order
    from apps.collections.models import PickupRequest
    from apps.impact.models import ImpactRecord
    from apps.notifications.email_service import EmailService

    admins = User.objects.filter(role='admin', is_active=True)
    if not admins.exists():
        return

    from django.utils import timezone
    from datetime import timedelta
    week_ago = timezone.now() - timedelta(days=7)

    stats = {
        'new_users': User.objects.filter(created_at__gte=week_ago).count(),
        'new_orders': Order.objects.filter(created_at__gte=week_ago).count(),
        'new_pickups': PickupRequest.objects.filter(created_at__gte=week_ago).count(),
        'kg_recycled': ImpactRecord.objects.filter(
            created_at__gte=week_ago
        ).aggregate(total=Sum('kg_recycled'))['total'] or 0,
    }

    html = (
        f"<h2>Rapport hebdomadaire EcoCycle Haiti</h2>"
        f"<ul>"
        f"<li>Nouveaux utilisateurs : {stats['new_users']}</li>"
        f"<li>Nouvelles commandes : {stats['new_orders']}</li>"
        f"<li>Nouvelles demandes de ramassage : {stats['new_pickups']}</li>"
        f"<li>KG recyclés cette semaine : {stats['kg_recycled']}</li>"
        f"</ul>"
    )
    for admin in admins:
        EmailService._send(admin.email, '[EcoCycle] Rapport hebdomadaire', html)
