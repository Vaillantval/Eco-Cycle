from django.contrib import admin
from .models import PickupRequest


@admin.register(PickupRequest)
class PickupRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'collector', 'city', 'preferred_date',
        'preferred_slot', 'status', 'actual_weight_kg', 'created_at',
    ]
    list_filter = ['status', 'preferred_slot', 'city']
    search_fields = [
        'user__email', 'user__first_name',
        'collector__email', 'city', 'address',
    ]
    readonly_fields = [
        'id', 'status_history', 'created_at', 'updated_at', 'completed_at',
    ]
    ordering = ['-created_at']

    fieldsets = (
        ('Utilisateur', {'fields': ('id', 'user', 'listing')}),
        ('Adresse & Créneau', {
            'fields': ('address', 'city', 'latitude', 'longitude',
                       'preferred_date', 'preferred_slot', 'special_instructions'),
        }),
        ('Collecteur', {'fields': ('collector',)}),
        ('Statut', {'fields': ('status', 'status_history')}),
        ('Résultat', {'fields': ('actual_weight_kg', 'collector_notes', 'completion_photo')}),
        ('Dates', {'fields': ('created_at', 'updated_at', 'completed_at')}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'collector', 'listing')
