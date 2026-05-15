from celery import shared_task


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
