from apps.waste.models import WasteListing
from apps.collections.models import PickupRequest


def admin_badges(request):
    if request.session.get('user_role') != 'admin':
        return {}
    return {
        'pending_listings_count': WasteListing.objects.filter(status='pending_review').count(),
        'pending_pickups_count':  PickupRequest.objects.filter(status='requested').count(),
    }
