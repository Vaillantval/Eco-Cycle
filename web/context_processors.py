from apps.waste.models import WasteListing
from apps.collections.models import PickupRequest
from apps.core.models import ContactMessage


def admin_badges(request):
    if request.session.get('user_role') != 'admin':
        return {}
    from apps.academy.models import CourseRecommendation
    from apps.blog.models import BlogRecommendation
    return {
        'pending_listings_count': WasteListing.objects.filter(status='pending_review').count(),
        'pending_pickups_count':  PickupRequest.objects.filter(status='requested').count(),
        'unread_contacts_count':  ContactMessage.objects.filter(is_read=False).count(),
        'pending_recommendations_count': (
            CourseRecommendation.objects.filter(status='pending').count()
            + BlogRecommendation.objects.filter(status='pending').count()
        ),
    }
