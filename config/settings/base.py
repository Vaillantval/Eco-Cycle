import os
from pathlib import Path
from datetime import timedelta
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-changeme-not-for-production')

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'drf_spectacular',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'django_celery_beat',
    'django_celery_results',

    # Local apps
    'apps.accounts',
    'apps.waste',
    'apps.marketplace',
    'apps.collections',
    'apps.notifications',
    'apps.impact',
    'apps.academy',
    'apps.blog',
    'apps.core',
    'apps.payments',
    'web',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'apps.core.middleware.MaintenanceModeMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'web.context_processors.admin_badges',
                'apps.core.context_processors.site_config',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_USER_MODEL = 'accounts.User'

_DATABASE_URL = config('DATABASE_URL', default='')
if _DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=_DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'America/Port-au-Prince'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'ai_analysis': '20/hour',
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'EcoCycle Haiti API',
    'DESCRIPTION': 'API REST pour la plateforme de recyclage intelligent EcoCycle Haiti.',
    'VERSION': 'v1',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SECURITY': [{'BearerAuth': []}],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/0'),
    }
}

RESEND_API_KEY = config('RESEND_API_KEY', default='')
RESEND_FROM_EMAIL = config('RESEND_FROM_EMAIL', default='noreply@ecocycle.ht')
RESEND_FROM_NAME = config('RESEND_FROM_NAME', default='EcoCycle Haiti')
YOUTUBE_API_KEY = config('YOUTUBE_API_KEY', default='')
ANTHROPIC_API_KEY          = config('ANTHROPIC_API_KEY',          default='').strip()
ANTHROPIC_AGENT_ID         = config('ANTHROPIC_AGENT_ID',         default='').strip()
ANTHROPIC_ADVISOR_AGENT_ID = config('ANTHROPIC_ADVISOR_AGENT_ID', default='').strip()
ANTHROPIC_ENV_ID           = config('ANTHROPIC_ENV_ID',           default='').strip()
FIREBASE_CREDENTIALS_PATH = config('FIREBASE_CREDENTIALS_PATH', default='firebase-credentials.json')
FIREBASE_CREDENTIALS_B64 = config('FIREBASE_CREDENTIALS_B64', default='')
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:8000')

# ── Stripe ────────────────────────────────────────────────────────────────────
STRIPE = {
    'PUBLIC_KEY':      config('STRIPE_PUBLIC_KEY', default=''),
    'SECRET_KEY':      config('STRIPE_SECRET_KEY', default=''),
    'WEBHOOK_SECRET':  config('STRIPE_WEBHOOK_SECRET', default=''),
}

# ── PlopPlop (MonCash / NatCash / Kashpaw) ────────────────────────────────────
PLOPPLOP = {
    'CLIENT_ID':  config('PLOPPLOP_CLIENT_ID', default=''),
    'BASE_URL':   'https://plopplop.solutionip.app',
    'RETURN_URL': config(
        'PLOPPLOP_RETURN_URL',
        default='http://localhost:8000/payment/plopplop/retour/',
    ),
}
ADMIN_EMAIL = config('ADMIN_EMAIL', default='admin@ecocycle.ht')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps.waste.ai_service': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

SESSION_COOKIE_AGE = 86400 * 7
SESSION_COOKIE_HTTPONLY = True

# ═══════════════════════════════════
#   JAZZMIN — Admin UI
# ═══════════════════════════════════
JAZZMIN_SETTINGS = {
    # Titre affiché dans l'onglet et la barre latérale
    "site_title": "EcoCycle Admin",
    "site_header": "EcoCycle Haiti",
    "site_brand": "♻️ EcoCycle",
    "welcome_sign": "Bienvenue sur le panel EcoCycle Haiti",
    "copyright": "EcoCycle Haiti © 2026",

    # Liens de recherche rapide en haut
    "search_model": ["accounts.User", "waste.WasteListing", "marketplace.Auction"],

    # Icônes par app
    "icons": {
        "accounts": "fas fa-users",
        "accounts.User": "fas fa-user",
        "waste": "fas fa-recycle",
        "waste.WasteListing": "fas fa-box-open",
        "waste.WasteCategory": "fas fa-tags",
        "marketplace": "fas fa-store",
        "marketplace.Auction": "fas fa-gavel",
        "marketplace.Bid": "fas fa-hand-paper",
        "marketplace.Order": "fas fa-shopping-cart",
        "collections": "fas fa-truck",
        "collections.PickupRequest": "fas fa-map-marker-alt",
        "impact": "fas fa-leaf",
        "impact.ImpactRecord": "fas fa-chart-line",
        "academy": "fas fa-graduation-cap",
        "academy.Course": "fas fa-book",
        "blog": "fas fa-newspaper",
        "blog.Article": "fas fa-pen",
        "core": "fas fa-envelope",
        "notifications": "fas fa-bell",
        "auth": "fas fa-shield-alt",
        "auth.Group": "fas fa-users-cog",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",

    # Liens utiles en haut à droite
    "topmenu_links": [
        {"name": "Site Web", "url": "/", "new_window": True, "icon": "fas fa-globe"},
        {"name": "API Docs", "url": "/api/docs/", "new_window": True, "icon": "fas fa-code"},
        {"model": "accounts.User"},
    ],

    # Liens dans le menu utilisateur (avatar en haut à droite)
    "usermenu_links": [
        {"name": "Site Web", "url": "/", "new_window": True},
        {"model": "accounts.User"},
    ],

    # Sidebar
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],

    # Ordre des apps dans la sidebar
    "order_with_respect_to": [
        "accounts",
        "waste",
        "marketplace",
        "collections",
        "impact",
        "academy",
        "blog",
        "core",
        "notifications",
    ],

    # Interface
    "related_modal_active": True,
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": True,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-success",   # vert EcoCycle
    "accent": "accent-success",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-success",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}
