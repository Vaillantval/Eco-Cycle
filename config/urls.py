from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from web.views.payment_views import StripeWebhookView, PlopPlopWebhookView

handler404 = 'web.error_views.page_not_found'
handler500 = 'web.error_views.server_error'


def health_check(request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    # Healthcheck Railway
    path('health/', health_check),

    # Web frontend (DOIT être en premier)
    path('', include('web.urls')),

    # Documentation API
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('admin/', admin.site.urls),

    # API v1
    path('api/auth/', include('apps.accounts.urls')),
    path('api/waste/', include('apps.waste.urls')),
    path('api/marketplace/', include('apps.marketplace.urls')),
    path('api/collections/', include('apps.collections.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/impact/', include('apps.impact.urls')),
    path('api/academy/', include('apps.academy.urls')),
    path('api/blog/', include('apps.blog.urls')),
    path('api/contact/', include('apps.core.urls')),
    path('api/newsletter/', include('apps.core.newsletter_urls')),

    # Webhooks paiement (CSRF-exempt, signature validée dans la vue)
    path('api/payments/stripe/webhook/',   StripeWebhookView.as_view(),   name='stripe_webhook'),
    path('api/payments/plopplop/webhook/', PlopPlopWebhookView.as_view(), name='plopplop_webhook'),
]

# Serve media files — django.conf.urls.static.static() returns [] when DEBUG=False
# so we wire django.views.static.serve directly.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
