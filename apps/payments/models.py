import uuid
import random
import string
from django.db import models
from django.utils import timezone
from django.db.models.signals import pre_save
from django.dispatch import receiver


def _generate_transaction_number():
    date_part = timezone.now().strftime('%Y%m%d')
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    candidate = f'EC-{date_part}-{suffix}'
    while Transaction.objects.filter(transaction_number=candidate).exists():
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        candidate = f'EC-{date_part}-{suffix}'
    return candidate


class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending',   'En attente'),
        ('completed', 'Complété'),
        ('failed',    'Échoué'),
        ('cancelled', 'Annulé'),
        ('refunded',  'Remboursé'),
    ]
    METHOD_CHOICES = [
        ('credit_card', 'Carte bancaire (Stripe)'),
        ('moncash',     'MonCash'),
        ('natcash',     'NatCash'),
        ('kashpaw',     'Kashpaw'),
    ]

    id                     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order                  = models.OneToOneField(
        'marketplace.Order', on_delete=models.CASCADE, related_name='transaction',
        null=True, blank=True,
    )
    enrollment             = models.OneToOneField(
        'academy.Enrollment', on_delete=models.CASCADE, related_name='transaction',
        null=True, blank=True,
    )
    transaction_number     = models.CharField(max_length=30, unique=True, blank=True)
    amount                 = models.DecimalField(max_digits=10, decimal_places=2)
    currency               = models.CharField(max_length=5, default='HTG')
    status                 = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method         = models.CharField(max_length=20, choices=METHOD_CHOICES, blank=True)
    external_transaction_id = models.CharField(max_length=255, blank=True)
    meta_data              = models.JSONField(default=dict)
    created_at             = models.DateTimeField(auto_now_add=True)
    updated_at             = models.DateTimeField(auto_now=True)
    completed_at           = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payment_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_number']),
            models.Index(fields=['external_transaction_id']),
        ]

    def __str__(self):
        return f'{self.transaction_number} — {self.amount} {self.currency} [{self.status}]'

    @property
    def is_refundable(self):
        return self.status == 'completed'


@receiver(pre_save, sender=Transaction)
def set_transaction_number(sender, instance, **kwargs):
    if not instance.transaction_number:
        instance.transaction_number = _generate_transaction_number()
