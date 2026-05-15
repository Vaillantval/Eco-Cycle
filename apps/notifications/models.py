from django.db import models
from django.conf import settings
import uuid


class Notification(models.Model):
    TYPE_CHOICES = [
        ('listing_approved', 'Listing approuvé'),
        ('listing_rejected', 'Listing rejeté'),
        ('new_bid', 'Nouvelle enchère'),
        ('auction_won', 'Enchère gagnée'),
        ('auction_lost', 'Enchère perdue'),
        ('auction_closed', 'Enchère clôturée'),
        ('order_created', 'Commande créée'),
        ('pickup_assigned', 'Ramassage assigné'),
        ('pickup_status', 'Statut ramassage'),
        ('pickup_completed', 'Ramassage complété'),
        ('new_listing_admin', 'Nouveau listing (admin)'),
        ('system', 'Système'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'
    )
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} — {self.title}'
