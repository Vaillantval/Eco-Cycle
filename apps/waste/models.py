from django.db import models
from django.conf import settings
import uuid


class WasteCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=10, blank=True)
    description = models.TextField(blank=True)
    base_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'waste_categories'
        verbose_name_plural = 'Waste Categories'

    def __str__(self):
        return self.name


class WasteListing(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('pending_review', 'En attente de révision'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('sold', 'Vendu'),
        ('collected', 'Collecté'),
        ('archived', 'Archivé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='waste_listings'
    )
    category = models.ForeignKey(
        WasteCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='listings'
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quantity_kg = models.DecimalField(max_digits=8, decimal_places=2, help_text='Poids estimé en kg')

    photo = models.ImageField(upload_to='waste_photos/')
    photo_url = models.URLField(blank=True)

    ai_analysis = models.JSONField(null=True, blank=True)
    ai_estimated_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ai_analyzed_at = models.DateTimeField(null=True, blank=True)

    pickup_address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_listings'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'waste_listings'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} — {self.user.full_name}'


class WastePhoto(models.Model):
    listing = models.ForeignKey(WasteListing, on_delete=models.CASCADE, related_name='additional_photos')
    photo = models.ImageField(upload_to='waste_photos/gallery/')
    order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'waste_photos'
        ordering = ['order']
