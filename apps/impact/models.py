from django.db import models
from django.conf import settings
import uuid

CO2_FACTORS = {
    'plastic': 1.5,
    'metal': 4.0,
    'paper': 0.9,
    'electronics': 20.0,
    'glass': 0.3,
    'tires': 2.8,
    'other': 0.5,
}


class ImpactRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='impact_records'
    )
    order = models.OneToOneField(
        'marketplace.Order', on_delete=models.CASCADE,
        related_name='impact', null=True, blank=True
    )
    pickup = models.OneToOneField(
        'collections.PickupRequest', on_delete=models.CASCADE,
        related_name='impact', null=True, blank=True
    )

    category_slug = models.CharField(max_length=50, blank=True)
    kg_recycled = models.DecimalField(max_digits=8, decimal_places=2)
    co2_saved_kg = models.DecimalField(max_digits=10, decimal_places=3)
    economic_value_htg = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'impact_records'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} — {self.kg_recycled} kg ({self.category_slug})'


class UserImpactSummary(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='impact_summary'
    )
    total_kg_recycled = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_co2_saved_kg = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    total_economic_value_htg = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_transactions = models.PositiveIntegerField(default=0)
    community_rank = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_impact_summaries'

    def __str__(self):
        return f'{self.user.email} — {self.total_kg_recycled} kg recyclés'
