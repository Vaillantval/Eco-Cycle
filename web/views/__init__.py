from django.views.generic import TemplateView
from django.db.models import Sum
from django.utils import timezone
from django.core.cache import cache
from apps.impact.models import ImpactRecord
from apps.accounts.models import User
from apps.marketplace.models import Auction
from apps.collections.models import PickupRequest


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        stats = cache.get('home_stats')
        if not stats:
            agg = ImpactRecord.objects.aggregate(
                total_kg=Sum('kg_recycled'),
                total_co2=Sum('co2_saved_kg'),
            )
            stats = {
                'total_kg_recycled': int(agg['total_kg'] or 0),
                'total_co2_saved':   int(agg['total_co2'] or 0),
                'total_users':       User.objects.filter(is_active=True).count(),
                'total_collections': PickupRequest.objects.filter(status='completed').count(),
            }
            cache.set('home_stats', stats, 300)

        context['stats'] = stats
        context['featured_auctions'] = (
            Auction.objects
            .filter(status='active', ends_at__gt=timezone.now())
            .select_related('listing', 'listing__category')
            .order_by('-created_at')[:6]
        )
        from apps.core.models import SliderItem
        context['slider_items'] = SliderItem.objects.filter(is_active=True).order_by('ordre')
        return context
