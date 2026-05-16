from django.contrib import admin
from django.utils.html import format_html
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display  = ('transaction_number', 'order_link', 'amount_display', 'payment_method', 'status_badge', 'created_at')
    list_filter   = ('status', 'payment_method', 'currency', 'created_at')
    search_fields = ('transaction_number', 'external_transaction_id', 'order__buyer__email')
    readonly_fields = (
        'id', 'transaction_number', 'order', 'created_at', 'updated_at', 'completed_at',
        'external_transaction_id', 'meta_data',
    )
    ordering = ('-created_at',)
    list_per_page = 25

    def order_link(self, obj):
        return format_html(
            '<a href="/admin/marketplace/order/{}/change/">#{}</a>',
            obj.order.id, str(obj.order.id)[:8],
        )
    order_link.short_description = 'Commande'

    def amount_display(self, obj):
        return f'{obj.amount} {obj.currency}'
    amount_display.short_description = 'Montant'

    def status_badge(self, obj):
        colors = {
            'pending':   ('#fef3c7', '#92400e'),
            'completed': ('#d1fae5', '#065f46'),
            'failed':    ('#fee2e2', '#991b1b'),
            'cancelled': ('#f3f4f6', '#374151'),
            'refunded':  ('#ede9fe', '#5b21b6'),
        }
        bg, color = colors.get(obj.status, ('#f3f4f6', '#374151'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;border-radius:12px;font-weight:600;font-size:0.78rem">{}</span>',
            bg, color, obj.get_status_display(),
        )
    status_badge.short_description = 'Statut'
