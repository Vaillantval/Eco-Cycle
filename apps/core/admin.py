from django.contrib import admin
from .models import ContactMessage, NewsletterSubscriber


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'subject', 'is_read', 'replied', 'created_at']
    list_filter = ['is_read', 'replied']
    search_fields = ['email', 'first_name', 'last_name', 'subject']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_confirmed', 'subscribed_at']
    list_filter = ['is_confirmed']
    search_fields = ['email']
    readonly_fields = ['id', 'token', 'subscribed_at']
    ordering = ['-subscribed_at']
