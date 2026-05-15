from rest_framework import serializers
from .models import Auction, Bid, Order
from apps.waste.serializers import WasteListingSerializer


class BidSerializer(serializers.ModelSerializer):
    bidder_name = serializers.ReadOnlyField(source='bidder.full_name')

    class Meta:
        model = Bid
        fields = ['id', 'bidder', 'bidder_name', 'amount', 'is_winning', 'created_at']
        read_only_fields = ['id', 'bidder', 'is_winning', 'created_at']


class AuctionSerializer(serializers.ModelSerializer):
    listing = WasteListingSerializer(read_only=True)
    seller_name = serializers.ReadOnlyField(source='seller.full_name')
    latest_bids = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    user_bid = serializers.SerializerMethodField()

    class Meta:
        model = Auction
        fields = [
            'id', 'listing', 'seller', 'seller_name',
            'auction_type', 'starting_price', 'buy_now_price',
            'current_price', 'reserve_price', 'status',
            'starts_at', 'ends_at', 'winner',
            'total_bids', 'views_count',
            'latest_bids', 'time_remaining', 'user_bid',
            'created_at',
        ]
        read_only_fields = ['id', 'seller', 'current_price', 'total_bids', 'views_count', 'winner']

    def get_latest_bids(self, obj):
        bids = obj.bids.order_by('-amount')[:5]
        return BidSerializer(bids, many=True).data

    def get_time_remaining(self, obj):
        from django.utils import timezone
        if obj.ends_at > timezone.now():
            delta = obj.ends_at - timezone.now()
            return int(delta.total_seconds())
        return 0

    def get_user_bid(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            bid = obj.bids.filter(bidder=request.user).order_by('-amount').first()
            if bid:
                return BidSerializer(bid).data
        return None


class CreateAuctionSerializer(serializers.ModelSerializer):
    listing_id = serializers.UUIDField()

    class Meta:
        model = Auction
        fields = [
            'listing_id', 'auction_type', 'starting_price',
            'buy_now_price', 'reserve_price', 'starts_at', 'ends_at',
        ]

    def validate_listing_id(self, value):
        from apps.waste.models import WasteListing
        try:
            listing = WasteListing.objects.get(
                id=value, user=self.context['request'].user, status='approved'
            )
            if hasattr(listing, 'auction'):
                raise serializers.ValidationError('Ce listing a déjà une enchère.')
            return value
        except WasteListing.DoesNotExist:
            raise serializers.ValidationError('Listing invalide ou non approuvé.')

    def create(self, validated_data):
        from apps.waste.models import WasteListing
        listing = WasteListing.objects.get(id=validated_data.pop('listing_id'))
        validated_data['seller'] = self.context['request'].user
        validated_data['listing'] = listing
        validated_data['current_price'] = validated_data['starting_price']
        return super().create(validated_data)


class PlaceBidSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_amount(self, value):
        auction = self.context.get('auction')
        if auction:
            min_bid = (auction.current_price or auction.starting_price) + 10
            if value < min_bid:
                raise serializers.ValidationError(
                    f"L'enchère minimale est {min_bid} HTG."
                )
        return value


class OrderSerializer(serializers.ModelSerializer):
    buyer_name = serializers.ReadOnlyField(source='buyer.full_name')
    seller_name = serializers.ReadOnlyField(source='seller.full_name')
    listing_title = serializers.ReadOnlyField(source='auction.listing.title')

    class Meta:
        model = Order
        fields = [
            'id', 'auction', 'buyer', 'buyer_name', 'seller', 'seller_name',
            'listing_title', 'amount', 'platform_fee', 'seller_payout',
            'status', 'notes', 'created_at', 'updated_at', 'completed_at',
        ]
        read_only_fields = ['id', 'buyer', 'seller', 'platform_fee', 'seller_payout']
