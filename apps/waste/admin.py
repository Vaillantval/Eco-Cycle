from django.contrib import admin
from .models import WasteCategory, WasteListing, WastePhoto


@admin.register(WasteCategory)
class WasteCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'base_price_per_kg', 'is_active']
    list_filter = ['is_active']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


class WastePhotoInline(admin.TabularInline):
    model = WastePhoto
    extra = 0
    readonly_fields = ['uploaded_at']


@admin.register(WasteListing)
class WasteListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'status', 'quantity_kg', 'ai_estimated_value', 'city', 'created_at']
    list_filter = ['status', 'category', 'city']
    search_fields = ['title', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'ai_analysis', 'ai_estimated_value', 'ai_analyzed_at', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at']
    ordering = ['-created_at']
    inlines = [WastePhotoInline]

    fieldsets = (
        ('Informations', {'fields': ('id', 'user', 'category', 'title', 'description', 'quantity_kg')}),
        ('Photo', {'fields': ('photo', 'photo_url')}),
        ('Analyse AI', {'fields': ('ai_analysis', 'ai_estimated_value', 'ai_analyzed_at')}),
        ('Localisation', {'fields': ('pickup_address', 'city', 'latitude', 'longitude')}),
        ('Statut', {'fields': ('status', 'rejection_reason', 'reviewed_by', 'reviewed_at')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
