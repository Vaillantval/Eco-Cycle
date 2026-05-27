from django.contrib import admin
from django.contrib import messages
from .models import WasteCategory, WasteListing, WastePhoto


def reanalyze_ai(modeladmin, request, queryset):
    from .tasks import analyze_waste_photo_async
    count = 0
    for listing in queryset.exclude(photo=''):
        analyze_waste_photo_async.delay(str(listing.id))
        count += 1
    modeladmin.message_user(request, f'{count} listing(s) envoyés en re-analyse IA.', messages.SUCCESS)

reanalyze_ai.short_description = '🤖 Re-analyser avec l\'IA'


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
    actions = [reanalyze_ai]
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
