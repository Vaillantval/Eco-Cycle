from django.contrib import admin
from django.shortcuts import redirect
from django.utils.html import format_html
from .models import SiteConfiguration, SliderItem, ContactMessage, NewsletterSubscriber


# ── SiteConfiguration (singleton) ────────────────────────────────────────────

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    save_on_top = True

    fieldsets = [
        ('🏷️ Identité', {
            'fields': ('site_name', 'tagline', 'logo', 'favicon'),
        }),
        ('🏠 Page d\'accueil — Hero', {
            'fields': ('hero_badge', 'hero_title_1', 'hero_title_2', 'hero_subtitle'),
            'classes': ('collapse',),
        }),
        ('📞 Contact & Coordonnées', {
            'fields': ('contact_email', 'contact_phone', 'whatsapp', 'address', 'hours'),
        }),
        ('🌐 Réseaux sociaux', {
            'fields': ('facebook_url', 'instagram_url', 'twitter_url', 'youtube_url', 'linkedin_url'),
            'classes': ('collapse',),
        }),
        ('📱 Application mobile', {
            'fields': ('android_direct_apk', 'ios_direct_ipa'),
            'classes': ('collapse',),
        }),
        ('🔍 SEO & Footer', {
            'fields': ('meta_description', 'google_analytics_id', 'copyright_text'),
            'classes': ('collapse',),
        }),
        ('🚧 Maintenance', {
            'fields': ('maintenance_mode', 'maintenance_message'),
            'classes': ('collapse',),
        }),
    ]

    def has_add_permission(self, request):
        return not SiteConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = SiteConfiguration.get_solo()
        return redirect(f'/admin/core/siteconfiguration/{obj.pk}/change/')

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="height:40px;border-radius:4px">', obj.logo.url)
        return '—'
    logo_preview.short_description = 'Aperçu logo'


# ── SliderItem ────────────────────────────────────────────────────────────────

@admin.register(SliderItem)
class SliderItemAdmin(admin.ModelAdmin):
    list_display  = ('title', 'image_preview', 'btn_text', 'ordre', 'is_active')
    list_editable = ('ordre', 'is_active')
    ordering      = ('ordre',)
    fields        = ('image', 'image_preview', 'title', 'subtitle', 'btn_text', 'btn_url', 'ordre', 'is_active')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:60px;border-radius:6px;object-fit:cover;width:120px;">',
                obj.image.url
            )
        return '—'
    image_preview.short_description = 'Aperçu'


# ── ContactMessage ────────────────────────────────────────────────────────────

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display    = ('full_name', 'email', 'subject', 'badge_read', 'badge_replied', 'created_at')
    list_filter     = ('is_read', 'replied', 'created_at')
    search_fields   = ('email', 'first_name', 'last_name', 'subject')
    readonly_fields = ('id', 'first_name', 'last_name', 'email', 'subject', 'message', 'created_at')
    ordering        = ('-created_at',)

    fieldsets = [
        ('Expéditeur', {'fields': ('first_name', 'last_name', 'email', 'created_at')}),
        ('Message',    {'fields': ('subject', 'message')}),
        ('Traitement', {'fields': ('is_read', 'replied')}),
    ]

    def full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'
    full_name.short_description = 'Nom'

    def badge_read(self, obj):
        if obj.is_read:
            return format_html('<span style="background:#d1fae5;color:#059669;padding:2px 10px;border-radius:12px;font-weight:600">Lu</span>')
        return format_html('<span style="background:#fef3c7;color:#d97706;padding:2px 10px;border-radius:12px;font-weight:600">Non lu</span>')
    badge_read.short_description = 'Lu'

    def badge_replied(self, obj):
        if obj.replied:
            return format_html('<span style="background:#dbeafe;color:#2563eb;padding:2px 10px;border-radius:12px;font-weight:600">Répondu</span>')
        return '—'
    badge_replied.short_description = 'Répondu'

    def has_add_permission(self, request):
        return False


# ── NewsletterSubscriber ──────────────────────────────────────────────────────

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display  = ('email', 'badge_confirmed', 'subscribed_at')
    list_filter   = ('is_confirmed',)
    search_fields = ('email',)
    readonly_fields = ('id', 'token', 'subscribed_at')
    ordering      = ('-subscribed_at',)

    def badge_confirmed(self, obj):
        if obj.is_confirmed:
            return format_html('<span style="background:#d1fae5;color:#059669;padding:2px 10px;border-radius:12px;font-weight:600">Confirmé</span>')
        return format_html('<span style="background:#fee2e2;color:#dc2626;padding:2px 10px;border-radius:12px;font-weight:600">En attente</span>')
    badge_confirmed.short_description = 'Statut'
