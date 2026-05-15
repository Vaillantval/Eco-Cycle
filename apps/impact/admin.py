from django.contrib import admin
from .models import ImpactRecord, UserImpactSummary


@admin.register(ImpactRecord)
class ImpactRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'category_slug', 'kg_recycled', 'co2_saved_kg', 'economic_value_htg', 'created_at']
    list_filter = ['category_slug']
    search_fields = ['user__email']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']


@admin.register(UserImpactSummary)
class UserImpactSummaryAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_kg_recycled', 'total_co2_saved_kg', 'total_transactions', 'community_rank', 'updated_at']
    search_fields = ['user__email']
    readonly_fields = ['updated_at']
    ordering = ['community_rank']
