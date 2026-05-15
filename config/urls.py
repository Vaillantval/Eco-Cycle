from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
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
