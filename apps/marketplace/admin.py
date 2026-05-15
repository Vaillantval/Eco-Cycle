from django.contrib import admin
from .models import Auction, Bid, Order


class BidInline(admin.TabularInline):
    model = Bid
    extra = 0
    readonly_fields = ['id', 'bidder', 'amount', 'is_winning', 'created_at']
    ordering = ['-amount']


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = [
        'listing', 'seller', 'auction_type', 'status',
        'current_price', 'total_bids', 'ends_at', 'created_at',
    ]
    list_filter = ['status', 'auction_type']
    search_fields = ['listing__title', 'seller__email']
    readonly_fields = ['id', 'total_bids', 'views_count', 'winner', 'created_at', 'updated_at']
    ordering = ['-created_at']
    inlines = [BidInline]

    fieldsets = (
        ('Enchère', {'fields': ('id', 'listing', 'seller', 'auction_type')}),
        ('Prix', {'fields': ('starting_price', 'buy_now_price', 'current_price', 'reserve_price')}),
        ('Statut & Dates', {'fields': ('status', 'starts_at', 'ends_at', 'winner')}),
        ('Stats', {'fields': ('total_bids', 'views_count', 'created_at', 'updated_at')}),
    )


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ['auction', 'bidder', 'amount', 'is_winning', 'created_at']
    list_filter = ['is_winning']
    search_fields = ['bidder__email', 'auction__listing__title']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'buyer', 'seller', 'amount', 'platform_fee',
        'seller_payout', 'status', 'created_at',
    ]
    list_filter = ['status']
    search_fields = ['buyer__email', 'seller__email', 'auction__listing__title']
    readonly_fields = ['id', 'platform_fee', 'seller_payout', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Commande', {'fields': ('id', 'auction', 'buyer', 'seller')}),
        ('Finances', {'fields': ('amount', 'platform_fee', 'seller_payout')}),
        ('Statut', {'fields': ('status', 'notes', 'completed_at')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
