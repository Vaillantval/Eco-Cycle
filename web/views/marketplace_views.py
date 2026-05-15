import json
from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from web.mixins import LoginRequiredMixin
from apps.marketplace.models import Auction, Bid, Order
from apps.waste.models import WasteCategory


class MarketplaceListView(View):
    def get(self, request):
        auctions = Auction.objects.filter(
            status='active', ends_at__gt=timezone.now()
        ).select_related('listing', 'listing__category', 'seller')

        category_slug = request.GET.get('category', '')
        city          = request.GET.get('city', '')
        sort          = request.GET.get('sort', '-created_at')

        if category_slug:
            auctions = auctions.filter(listing__category__slug=category_slug)
        if city:
            auctions = auctions.filter(listing__city__icontains=city)

        sort_map = {
            'price_asc':  'current_price',
            'price_desc': '-current_price',
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
        auction = get_object_or_404(Auction, pk=pk)
        user    = self.get_current_user(request)

        # Accepte JSON ou form-data
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

        if not auction.is_active:
            return JsonResponse({'error': 'Enchère clôturée.'}, status=400)
        if auction.seller == user:
            return JsonResponse({'error': 'Vous ne pouvez pas enchérir sur votre propre listing.'}, status=400)

        min_bid = float(auction.current_price or auction.starting_price) + 10
        if amount < min_bid:
            return JsonResponse({'error': f'Enchère minimum : {min_bid:.0f} HTG.'}, status=400)

        auction.bids.filter(is_winning=True).update(is_winning=False)
        bid = Bid.objects.create(auction=auction, bidder=user, amount=amount, is_winning=True)
        auction.current_price = amount
        auction.total_bids   += 1
        auction.save()

        from apps.notifications.tasks import notify_new_bid
        notify_new_bid.delay(str(bid.id))

        return JsonResponse({
            'success':    True,
            'new_price':  str(amount),
            'total_bids': auction.total_bids,
        })


class BuyNowWebView(LoginRequiredMixin, View):
    def post(self, request, pk):
        auction = get_object_or_404(Auction, pk=pk)
        user    = self.get_current_user(request)

        if not auction.is_active or not auction.buy_now_price:
            messages.error(request, 'Achat immédiat non disponible.')
            return redirect('auction_detail', pk=pk)
        if auction.seller == user:
            messages.error(request, 'Vous ne pouvez pas acheter votre propre listing.')
            return redirect('auction_detail', pk=pk)

        auction.status = 'sold'
        auction.winner = user
        auction.save()

        order = Order.objects.create(
            auction=auction,
            buyer=user,
            seller=auction.seller,
            amount=auction.buy_now_price,
        )
        from apps.notifications.tasks import notify_order_created
        from apps.impact.tasks import create_impact_record
        notify_order_created.delay(str(order.id))
        create_impact_record.delay(str(order.id))

        messages.success(request, f'Achat confirmé ! Commande #{str(order.id)[:8]}')
        return redirect('my_orders')
