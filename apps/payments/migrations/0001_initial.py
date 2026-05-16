import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('marketplace', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('transaction_number', models.CharField(blank=True, max_length=30, unique=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='HTG', max_length=5)),
                ('status', models.CharField(
                    choices=[
                        ('pending',   'En attente'),
                        ('completed', 'Complété'),
                        ('failed',    'Échoué'),
                        ('cancelled', 'Annulé'),
                        ('refunded',  'Remboursé'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('payment_method', models.CharField(
                    blank=True,
                    choices=[
                        ('credit_card', 'Carte bancaire (Stripe)'),
                        ('moncash',     'MonCash'),
                        ('natcash',     'NatCash'),
                        ('kashpaw',     'Kashpaw'),
                    ],
                    max_length=20,
                )),
                ('external_transaction_id', models.CharField(blank=True, max_length=255)),
                ('meta_data', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('order', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='transaction',
                    to='marketplace.order',
                )),
            ],
            options={
                'db_table': 'payment_transactions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['-created_at'], name='pay_tx_created_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['status'], name='pay_tx_status_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['transaction_number'], name='pay_tx_number_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['external_transaction_id'], name='pay_tx_ext_id_idx'),
        ),
    ]
