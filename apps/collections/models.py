from django.db import models
from django.conf import settings
import uuid


class PickupRequest(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Demandé'),
        ('assigned', 'Assigné'),
        ('in_transit', 'En transit'),
        ('arrived', 'Arrivé'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
    ]

    SLOT_CHOICES = [
        ('morning', 'Matin (8h-12h)'),
        ('afternoon', 'Après-midi (12h-17h)'),
        ('evening', 'Soir (17h-20h)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pickup_requests'
    )
    listing = models.ForeignKey(
        'waste.WasteListing', on_delete=models.CASCADE,
        related_name='pickup_requests', null=True, blank=True
    )
    collector = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_pickups'
    )

    address = models.TextField()
    city = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    preferred_date = models.DateField()
    preferred_slot = models.CharField(max_length=20, choices=SLOT_CHOICES)
    special_instructions = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    status_history = models.JSONField(default=list)

    actual_weight_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    collector_notes = models.TextField(blank=True)
    completion_photo = models.ImageField(upload_to='pickups/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'pickup_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f'Pickup #{self.id} — {self.user.full_name} ({self.status})'

    def update_status(self, new_status, note=''):
        from django.utils import timezone
        self.status = new_status
        self.status_history.append({
            'status': new_status,
            'timestamp': timezone.now().isoformat(),
            'note': note,
        })
        if new_status == 'completed':
            self.completed_at = timezone.now()
        self.save()
