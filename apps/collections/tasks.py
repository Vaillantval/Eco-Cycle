from celery import shared_task


@shared_task(name='collections.auto_cancel_unassigned')
def auto_cancel_unassigned_pickups():
    """Annuler les demandes non assignées après 72h."""
    from django.utils import timezone
    from datetime import timedelta
    from .models import PickupRequest

    threshold = timezone.now() - timedelta(hours=72)
    stale = PickupRequest.objects.filter(
        status='requested',
        created_at__lt=threshold,
    )
    for pickup in stale:
        pickup.update_status('cancelled', 'Annulé automatiquement — aucun collecteur assigné.')
