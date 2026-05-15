from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

handler404 = 'web.error_views.page_not_found'
handler500 = 'web.error_views.server_error'

urlpatterns = [
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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
