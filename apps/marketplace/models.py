from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import uuid


class Auction(models.Model):
    TYPE_CHOICES = [
        ('auction', 'Enchère'),
        ('buy_now', 'Achat immédiat'),
        ('both', 'Enchère + Achat immédiat'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Clôturée'),
        ('sold', 'Vendue'),
        ('cancelled', 'Annulée'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.OneToOneField(
        'waste.WasteListing', on_delete=models.CASCADE, related_name='auction'
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='auctions'
    )

    auction_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='both')
    starting_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    buy_now_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reserve_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()

    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='won_auctions'
    )
    total_bids = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'auctions'
        ordering = ['-created_at']

    def __str__(self):
        return f'Auction — {self.listing.title}'

    @property
    def current_bid(self):
        return self.current_price or self.starting_price

    @property
    def is_active(self):
        from django.utils import timezone
        return self.status == 'active' and self.ends_at > timezone.now()


class Bid(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bids'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_winning = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bids'
        ordering = ['-amount']

    def __str__(self):
        return f'{self.bidder.full_name} — {self.amount} HTG'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending_payment', 'En attente de paiement'),
        ('paid', 'Payé'),
        ('processing', 'En traitement'),
        ('pickup_scheduled', 'Ramassage planifié'),
        ('completed', 'Complété'),
        ('cancelled', 'Annulé'),
        ('refunded', 'Remboursé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auction = models.OneToOneField(Auction, on_delete=models.CASCADE, related_name='order')
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders'
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sales'
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    seller_payout = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self.platform_fee = self.amount * 10 / 100
        self.seller_payout = self.amount - self.platform_fee
        super().save(*args, **kwargs)
