from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from .models import Auction, Bid, Order
from .serializers import (
    AuctionSerializer, CreateAuctionSerializer,
    PlaceBidSerializer, OrderSerializer, BidSerializer,
)
from apps.accounts.permissions import IsAdmin


class PublicAuctionListView(generics.ListAPIView):
    """GET /api/marketplace/auctions/"""
    serializer_class = AuctionSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['status', 'auction_type', 'listing__category']
    search_fields = ['listing__title', 'listing__description']
    ordering_fields = ['created_at', 'ends_at', 'current_price', 'total_bids']

    def get_queryset(self):
        return Auction.objects.filter(
            status='active',
            starts_at__lte=timezone.now(),
        ).select_related('listing', 'listing__category', 'seller')


class AuctionDetailView(generics.RetrieveAPIView):
    """GET /api/marketplace/auctions/<id>/"""
    serializer_class = AuctionSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Auction.objects.select_related('listing', 'seller')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Auction.objects.filter(pk=instance.pk).update(views_count=instance.views_count + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class CreateAuctionView(generics.CreateAPIView):
    """POST /api/marketplace/auctions/create/"""
    serializer_class = CreateAuctionSerializer
    permission_classes = [permissions.IsAuthenticated]


class PlaceBidView(APIView):
    """POST /api/marketplace/auctions/<id>/bid/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        with transaction.atomic():
            auction = get_object_or_404(
                Auction.objects.select_for_update(), pk=pk
            )

            if not auction.is_active:
                return Response(
                    {'error': 'Cette enchère est clôturée.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if auction.auction_type == 'buy_now':
                return Response(
                    {'error': 'Cette annonce est en achat immédiat uniquement.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if auction.seller == request.user:
                return Response(
                    {'error': 'Vous ne pouvez pas enchérir sur votre propre listing.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = PlaceBidSerializer(data=request.data, context={'auction': auction})
            serializer.is_valid(raise_exception=True)
            amount = serializer.validated_data['amount']

            auction.bids.filter(is_winning=True).update(is_winning=False)
            bid = Bid.objects.create(
                auction=auction, bidder=request.user, amount=amount, is_winning=True
            )
            auction.current_price = amount
            auction.total_bids += 1
            auction.save(update_fields=['current_price', 'total_bids', 'updated_at'])

        from apps.notifications.tasks import notify_new_bid
        notify_new_bid.delay(str(bid.id))

        return Response(BidSerializer(bid).data, status=status.HTTP_201_CREATED)


class BuyNowView(APIView):
    """POST /api/marketplace/auctions/<id>/buy-now/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        with transaction.atomic():
            auction = get_object_or_404(
                Auction.objects.select_for_update(), pk=pk
            )

            if not auction.is_active:
                return Response(
                    {'error': "Cette enchère n'est plus disponible."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if auction.auction_type == 'auction':
                return Response(
                    {'error': "L'achat immédiat n'est pas disponible pour cette enchère."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not auction.buy_now_price:
                return Response(
                    {'error': 'Achat immédiat non disponible.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if auction.seller == request.user:
                return Response(
                    {'error': 'Vous ne pouvez pas acheter votre propre listing.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            auction.status = 'sold'
            auction.winner = request.user
            auction.save(update_fields=['status', 'winner', 'updated_at'])

            order = Order.objects.create(
                auction=auction,
                buyer=request.user,
                seller=auction.seller,
                amount=auction.buy_now_price,
            )

        from apps.notifications.tasks import notify_order_created
        from apps.impact.tasks import create_impact_record
        notify_order_created.delay(str(order.id))
        create_impact_record.delay(str(order.id))

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class MyOrdersView(generics.ListAPIView):
    """GET /api/marketplace/orders/my/"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user).select_related('auction', 'seller')


class MySalesView(generics.ListAPIView):
    """GET /api/marketplace/orders/sales/"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(seller=self.request.user).select_related('auction', 'buyer')


class AdminOrderListView(generics.ListAPIView):
    """GET /api/marketplace/admin/orders/"""
    serializer_class = OrderSerializer
    permission_classes = [IsAdmin]
    queryset = Order.objects.select_related('auction', 'buyer', 'seller').all()
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'amount']
