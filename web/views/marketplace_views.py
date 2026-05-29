import json
from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import transaction
from web.mixins import LoginRequiredMixin
from apps.marketplace.models import Auction, Bid, Order
from apps.waste.models import WasteCategory
from apps.accounts.geocoding_service import haversine_distance


class MarketplaceListView(View):
    def get(self, request):
        auctions = Auction.objects.filter(
            status='active', ends_at__gt=timezone.now()
        ).select_related('listing', 'listing__category', 'seller')

        category_slug = request.GET.get('category', '')
        city          = request.GET.get('city', '')
        sort          = request.GET.get('sort', '-created_at')
        max_km_str    = request.GET.get('distance', '')

        if category_slug:
            auctions = auctions.filter(listing__category__slug=category_slug)
        if city:
            auctions = auctions.filter(listing__city__icontains=city)

        # Filtre par distance — nécessite la position de l'utilisateur
        user_lat = user_lon = None
        distance_active = False
        if max_km_str and request.session.get('user_id'):
            try:
                max_km = float(max_km_str)
                from apps.accounts.models import User as _User
                u = _User.objects.filter(id=request.session['user_id']).values('latitude', 'longitude').first()
                if u and u['latitude'] and u['longitude']:
                    user_lat = float(u['latitude'])
                    user_lon = float(u['longitude'])
                    # Pré-filtre bounding box (±max_km/111 degrés)
                    deg = max_km / 111.0
                    auctions = auctions.filter(
                        listing__latitude__range=(user_lat - deg, user_lat + deg),
                        listing__longitude__range=(user_lon - deg, user_lon + deg),
                    )
                    # Filtre exact haversine en Python
                    auctions = [
                        a for a in auctions
                        if a.listing.latitude and a.listing.longitude and
                        haversine_distance(user_lat, user_lon,
                                           float(a.listing.latitude),
                                           float(a.listing.longitude)) <= max_km
                    ]
                    distance_active = True
            except (ValueError, TypeError):
                pass

        if not distance_active:
            sort_map = {
                'price_asc':   'current_price',
                'price_desc':  '-current_price',
                'ending_soon': 'ends_at',
                '-created_at': '-created_at',
            }
            auctions = auctions.order_by(sort_map.get(sort, '-created_at'))

        paginator = Paginator(auctions, 12)
        page = paginator.get_page(request.GET.get('page', 1))

        return render(request, 'marketplace/list.html', {
            'auctions': page,
            'categories': WasteCategory.objects.filter(is_active=True),
            'active_category': category_slug,
            'active_sort': sort,
            'city_filter': city,
            'distance_filter': max_km_str,
            'distance_active': distance_active,
        })


class AuctionDetailView(View):
    def get(self, request, pk):
        auction = get_object_or_404(
            Auction.objects.select_related('listing', 'listing__category', 'seller'),
            pk=pk,
        )
        Auction.objects.filter(pk=pk).update(views_count=auction.views_count + 1)

        bids     = auction.bids.order_by('-amount')[:10]
        user_bid = None
        if request.session.get('user_id'):
            user_bid = auction.bids.filter(
                bidder_id=request.session['user_id']
            ).order_by('-amount').first()

        return render(request, 'marketplace/detail.html', {
            'auction':   auction,
            'bids':      bids,
            'user_bid':  user_bid,
            'is_owner':  str(auction.seller.id) == request.session.get('user_id', ''),
        })


class PlaceBidWebView(LoginRequiredMixin, View):
    """AJAX POST — retourne JSON."""
    def post(self, request, pk):
        user = self.get_current_user(request)

        if request.content_type and 'application/json' in request.content_type:
            try:
                payload = json.loads(request.body)
                amount  = float(payload.get('amount', 0))
            except (ValueError, json.JSONDecodeError):
                return JsonResponse({'error': 'Montant invalide.'}, status=400)
        else:
            try:
                amount = float(request.POST.get('amount', 0))
            except ValueError:
                return JsonResponse({'error': 'Montant invalide.'}, status=400)

        with transaction.atomic():
            auction = get_object_or_404(Auction.objects.select_for_update(), pk=pk)

            if not auction.is_active:
                return JsonResponse({'error': 'Enchère clôturée.'}, status=400)
            if auction.auction_type == 'buy_now':
                return JsonResponse({'error': 'Cette annonce est en achat immédiat uniquement.'}, status=400)
            if auction.seller == user:
                return JsonResponse({'error': 'Vous ne pouvez pas enchérir sur votre propre listing.'}, status=400)

            min_bid = float(auction.current_price or auction.starting_price) + 10
            if amount < min_bid:
                return JsonResponse({'error': f'Enchère minimum : {min_bid:.0f} HTG.'}, status=400)

            auction.bids.filter(is_winning=True).update(is_winning=False)
            bid = Bid.objects.create(auction=auction, bidder=user, amount=amount, is_winning=True)
            auction.current_price = amount
            auction.total_bids   += 1
            auction.save(update_fields=['current_price', 'total_bids', 'updated_at'])

        from apps.notifications.tasks import notify_new_bid
        notify_new_bid.delay(str(bid.id))

        return JsonResponse({
            'success':    True,
            'new_price':  str(amount),
            'total_bids': auction.total_bids,
        })


class BuyNowWebView(LoginRequiredMixin, View):
    def post(self, request, pk):
        user = self.get_current_user(request)

        with transaction.atomic():
            auction = get_object_or_404(Auction.objects.select_for_update(), pk=pk)

            if not auction.is_active:
                messages.error(request, "Cette enchère n'est plus disponible.")
                return redirect('auction_detail', pk=pk)
            if auction.auction_type == 'auction':
                messages.error(request, "L'achat immédiat n'est pas disponible pour cette enchère.")
                return redirect('auction_detail', pk=pk)
            if not auction.buy_now_price:
                messages.error(request, 'Achat immédiat non disponible.')
                return redirect('auction_detail', pk=pk)
            if auction.seller == user:
                messages.error(request, 'Vous ne pouvez pas acheter votre propre listing.')
                return redirect('auction_detail', pk=pk)

            auction.status = 'sold'
            auction.winner = user
            auction.save(update_fields=['status', 'winner', 'updated_at'])

            order = Order.objects.create(
                auction=auction,
                buyer=user,
                seller=auction.seller,
                amount=auction.buy_now_price,
            )

        from apps.notifications.tasks import notify_order_created
        notify_order_created.delay(str(order.id))

        return redirect('payment_checkout', order_id=order.id)
