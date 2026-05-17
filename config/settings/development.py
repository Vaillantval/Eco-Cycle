from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# En développement, WhiteNoise lit directement depuis STATICFILES_DIRS (static/)
# → plus besoin de collectstatic après chaque modif CSS/JS
WHITENOISE_USE_FINDERS = True

CORS_ALLOW_ALL_ORIGINS = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Use in-memory cache in dev (no Redis required)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Use db as Celery result backend — no broker needed in dev for sync tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = False
