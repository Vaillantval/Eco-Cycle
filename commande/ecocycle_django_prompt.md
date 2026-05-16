# EcoCycle — Prompt d'Implémentation Django Complet

> **Projet** : EcoCycle Haiti — Plateforme web + API REST pour application mobile Flutter  
> **Stack** : Django 5.x · DRF · PostgreSQL · Celery · Redis · Resend · Firebase FCM · Claude Vision API · Cloudinary · Railway  
> **Auteur** : Eliézer Léonce  

---

## TABLE DES MATIÈRES

1. [Vue d'ensemble](#1-vue-densemble)
2. [Arborescence du projet](#2-arborescence-du-projet)
3. [Requirements](#3-requirements)
4. [Variables d'environnement](#4-variables-denvironnement)
5. [Configuration Django (Settings)](#5-configuration-django-settings)
6. [Configuration Celery](#6-configuration-celery)
7. [App — accounts](#7-app--accounts)
8. [App — waste](#8-app--waste)
9. [App — marketplace](#9-app--marketplace)
10. [App — collections](#10-app--collections)
11. [App — notifications](#11-app--notifications)
12. [App — impact](#12-app--impact)
13. [App — academy](#13-app--academy)
14. [App — blog](#14-app--blog)
15. [App — core](#15-app--core)
16. [Services externes](#16-services-externes)
17. [URLs globales](#17-urls-globales)
18. [Déploiement Railway](#18-déploiement-railway)
19. [Commandes de setup](#19-commandes-de-setup)

---

## 1. Vue d'ensemble

EcoCycle est une plateforme de recyclage intelligente destinée à Haïti. Les utilisateurs photographient leurs déchets via l'application mobile Flutter. Un agent AI (Claude Vision) analyse la photo, identifie le type de déchet et lui attribue une valeur économique. L'utilisateur peut ensuite publier ce déchet sur la marketplace sous forme d'enchère ou de vente directe. Les admins sont notifiés et gèrent le cycle complet.

### Rôles utilisateurs

| Rôle | Description |
|---|---|
| `user` | Utilisateur standard — soumet des déchets, enchérit, suit son impact |
| `collector` | Ramasseur — reçoit et traite les demandes de collecte |
| `admin` | Administrateur — approuve les listings, gère tout |

### Flux principal

```
Photo (mobile) → Claude Vision API → WasteListing (draft)
→ Admin approve → Marketplace (Auction/BuyNow)
→ Transaction finalisée → ImpactRecord + Notifications
```

---

## 2. Arborescence du projet

```
ecocycle/
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py
├── apps/
│   ├── accounts/
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── permissions.py
│   │   └── tasks.py
│   ├── waste/
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── tasks.py
│   │   └── ai_service.py
│   ├── marketplace/
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tasks.py
│   ├── collections/
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tasks.py
│   ├── notifications/
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── email_service.py
│   │   └── fcm_service.py
│   ├── impact/
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── academy/
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── blog/
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   └── core/
│       ├── migrations/
│       ├── __init__.py
│       ├── admin.py
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
├── templates/
│   └── emails/
│       ├── base_email.html
│       ├── welcome.html
│       ├── verify_email.html
│       ├── reset_password.html
│       ├── listing_approved.html
│       ├── auction_won.html
│       ├── pickup_confirmed.html
│       └── newsletter_confirm.html
├── static/
├── media/
├── .env
├── .env.example
├── .gitignore
├── manage.py
├── requirements.txt
├── Procfile
└── railway.toml
```

---

## 3. Requirements

```txt
# requirements.txt

# Framework
Django==5.1.4
djangorestframework==3.15.2
django-cors-headers==4.4.0
django-filter==24.3

# Auth
djangorestframework-simplejwt==5.3.1
dj-rest-auth==6.0.0

# Base de données
psycopg2-binary==2.9.9
dj-database-url==2.2.0

# Tâches asynchrones
celery==5.4.0
redis==5.1.1
django-celery-beat==2.7.0
django-celery-results==2.5.1

# Stockage media
cloudinary==1.41.0
django-cloudinary-storage==0.3.0

# Email
resend==2.4.0

# Firebase FCM
firebase-admin==6.5.0

# Claude AI
anthropic==0.34.2

# Utilitaires
Pillow==10.4.0
python-decouple==3.8
whitenoise==6.7.0
gunicorn==22.0.0
django-extensions==3.2.3
django-storages==1.14.4

# Slugs
python-slugify==8.0.4

# Sécurité
django-ratelimit==4.1.0
```

---

## 4. Variables d'environnement

```bash
# .env.example

# Django
SECRET_KEY=your-very-secret-key-here
DEBUG=True
DJANGO_SETTINGS_MODULE=config.settings.development
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données (Railway fournit DATABASE_URL automatiquement)
DATABASE_URL=postgresql://user:password@host:5432/ecocycle

# Redis (Railway fournit REDIS_URL automatiquement)
REDIS_URL=redis://localhost:6379/0

# Cloudinary (stockage des photos)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Resend (emails transactionnels)
RESEND_API_KEY=re_your_resend_api_key
RESEND_FROM_EMAIL=noreply@ecocycle.ht
RESEND_FROM_NAME=EcoCycle Haiti

# Firebase FCM (push notifications)
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
# OU en base64 pour Railway :
FIREBASE_CREDENTIALS_B64=base64_encoded_firebase_json

# Anthropic Claude (analyse AI des déchets)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Frontend URLs
FRONTEND_URL=https://ecocycle.ht
MOBILE_DEEP_LINK=ecocycle://

# Email admin
ADMIN_EMAIL=admin@ecocycle.ht
```

---

## 5. Configuration Django (Settings)

### config/settings/base.py

```python
import os
from pathlib import Path
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'cloudinary',
    'cloudinary_storage',
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
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Auth
AUTH_USER_MODEL = 'accounts.User'

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
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

# Static & Media
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': config('CLOUDINARY_API_KEY'),
    'API_SECRET': config('CLOUDINARY_API_SECRET'),
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
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
        'ai_analysis': '20/hour',  # throttle spécial pour l'endpoint AI
    },
}

# JWT
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Celery
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Redis Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/0'),
    }
}

# Services externes
RESEND_API_KEY = config('RESEND_API_KEY')
RESEND_FROM_EMAIL = config('RESEND_FROM_EMAIL', default='noreply@ecocycle.ht')
RESEND_FROM_NAME = config('RESEND_FROM_NAME', default='EcoCycle Haiti')
ANTHROPIC_API_KEY = config('ANTHROPIC_API_KEY')
FIREBASE_CREDENTIALS_PATH = config('FIREBASE_CREDENTIALS_PATH', default='firebase-credentials.json')
FIREBASE_CREDENTIALS_B64 = config('FIREBASE_CREDENTIALS_B64', default='')
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:8000')
ADMIN_EMAIL = config('ADMIN_EMAIL', default='admin@ecocycle.ht')
```

### config/settings/development.py

```python
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

CORS_ALLOW_ALL_ORIGINS = True

# Email en dev — afficher dans la console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### config/settings/production.py

```python
from .base import *

DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    cast=lambda v: [s.strip() for s in v.split(',')],
    default='https://ecocycle.ht'
)

# Sécurité
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## 6. Configuration Celery

### config/celery.py

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

app = Celery('ecocycle')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Tâches périodiques
app.conf.beat_schedule = {
    # Clôturer les enchères expirées toutes les 5 minutes
    'close-expired-auctions': {
        'task': 'apps.marketplace.tasks.close_expired_auctions',
        'schedule': 300.0,
    },
    # Envoyer le rapport hebdo aux admins
    'weekly-admin-report': {
        'task': 'apps.core.tasks.send_weekly_report',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),
    },
}
```

### config/__init__.py

```python
from .celery import app as celery_app
__all__ = ('celery_app',)
```

---

## 7. App — accounts

### apps/accounts/models.py

```python
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
import uuid


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email obligatoire')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('user', 'Utilisateur'),
        ('collector', 'Ramasseur'),
        ('admin', 'Administrateur'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

    # Profil
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)

    # Statuts
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    # FCM Token pour push notifications (Flutter)
    fcm_token = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} <{self.email}>'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_collector(self):
        return self.role == 'collector'


class EmailVerificationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_token')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() < self.created_at + timedelta(hours=24)


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def is_valid(self):
        from django.utils import timezone
        from datetime import timedelta
        return not self.used and timezone.now() < self.created_at + timedelta(hours=2)
```

### apps/accounts/serializers.py

```python
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'password', 'password_confirm']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': 'Les mots de passe ne correspondent pas.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    total_listings = serializers.SerializerMethodField()
    total_kg_recycled = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone',
            'role', 'avatar', 'bio', 'address', 'city',
            'is_email_verified', 'full_name',
            'total_listings', 'total_kg_recycled',
            'created_at',
        ]
        read_only_fields = ['id', 'email', 'role', 'is_email_verified', 'created_at']

    def get_total_listings(self, obj):
        return obj.waste_listings.count()

    def get_total_kg_recycled(self, obj):
        from apps.impact.models import ImpactRecord
        from django.db.models import Sum
        result = ImpactRecord.objects.filter(user=obj).aggregate(total=Sum('kg_recycled'))
        return result['total'] or 0.0


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'bio', 'address', 'city', 'avatar']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Mot de passe actuel incorrect.')
        return value


class FCMTokenSerializer(serializers.Serializer):
    fcm_token = serializers.CharField(required=True)


class ResetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordConfirmSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(validators=[validate_password])
```

### apps/accounts/views.py

```python
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.shortcuts import get_object_or_404
from .models import User, EmailVerificationToken, PasswordResetToken
from .serializers import (
    RegisterSerializer, UserProfileSerializer, UpdateProfileSerializer,
    ChangePasswordSerializer, FCMTokenSerializer,
    ResetPasswordRequestSerializer, ResetPasswordConfirmSerializer
)
from .tasks import send_verification_email, send_password_reset_email


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/"""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Envoyer l'email de vérification (tâche Celery)
        send_verification_email.delay(str(user.id))

        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            'message': 'Compte créé. Vérifiez votre email.'
        }, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    """GET /api/auth/verify-email/<token>/"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        verification = get_object_or_404(EmailVerificationToken, token=token)
        if not verification.is_valid():
            return Response({'error': 'Token expiré.'}, status=status.HTTP_400_BAD_REQUEST)
        verification.user.is_email_verified = True
        verification.user.save()
        verification.delete()
        return Response({'message': 'Email vérifié avec succès.'})


class LoginView(APIView):
    """POST /api/auth/login/"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from django.contrib.auth import authenticate
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, username=email, password=password)
        if not user:
            return Response({'error': 'Identifiants invalides.'}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        })


class LogoutView(APIView):
    """POST /api/auth/logout/"""
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Déconnexion réussie.'})
        except Exception:
            return Response({'error': 'Token invalide.'}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    """GET/PUT/PATCH /api/auth/profile/"""
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UpdateProfileSerializer
        return UserProfileSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """POST /api/auth/change-password/"""
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'message': 'Mot de passe modifié.'})


class UpdateFCMTokenView(APIView):
    """POST /api/auth/fcm-token/"""
    def post(self, request):
        serializer = FCMTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.fcm_token = serializer.validated_data['fcm_token']
        request.user.save()
        return Response({'message': 'Token FCM mis à jour.'})


class ResetPasswordRequestView(APIView):
    """POST /api/auth/reset-password/"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            send_password_reset_email.delay(str(user.id))
        except User.DoesNotExist:
            pass  # Sécurité : ne pas révéler si l'email existe
        return Response({'message': 'Si cet email existe, un lien de réinitialisation a été envoyé.'})


class ResetPasswordConfirmView(APIView):
    """POST /api/auth/reset-password/confirm/"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reset_token = get_object_or_404(PasswordResetToken, token=serializer.validated_data['token'])
        if not reset_token.is_valid():
            return Response({'error': 'Token expiré ou déjà utilisé.'}, status=status.HTTP_400_BAD_REQUEST)
        reset_token.user.set_password(serializer.validated_data['new_password'])
        reset_token.user.save()
        reset_token.used = True
        reset_token.save()
        return Response({'message': 'Mot de passe réinitialisé.'})
```

### apps/accounts/permissions.py

```python
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'admin'


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return obj.user == request.user


class IsCollector(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['collector', 'admin']
```

### apps/accounts/tasks.py

```python
from celery import shared_task
from django.conf import settings
from .models import User, EmailVerificationToken, PasswordResetToken


@shared_task(name='accounts.send_verification_email')
def send_verification_email(user_id: str):
    from apps.notifications.email_service import EmailService
    try:
        user = User.objects.get(id=user_id)
        token, _ = EmailVerificationToken.objects.get_or_create(user=user)
        verify_url = f"{settings.FRONTEND_URL}/verify-email/{token.token}"
        EmailService.send_welcome(user=user, verify_url=verify_url)
    except User.DoesNotExist:
        pass


@shared_task(name='accounts.send_password_reset_email')
def send_password_reset_email(user_id: str):
    from apps.notifications.email_service import EmailService
    try:
        user = User.objects.get(id=user_id)
        token = PasswordResetToken.objects.create(user=user)
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{token.token}"
        EmailService.send_password_reset(user=user, reset_url=reset_url)
    except User.DoesNotExist:
        pass
```

### apps/accounts/urls.py

```python
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-email/<uuid:token>/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('fcm-token/', views.UpdateFCMTokenView.as_view(), name='fcm_token'),
    path('reset-password/', views.ResetPasswordRequestView.as_view(), name='reset_password_request'),
    path('reset-password/confirm/', views.ResetPasswordConfirmView.as_view(), name='reset_password_confirm'),
]
```

---

## 8. App — waste

### apps/waste/models.py

```python
from django.db import models
from django.conf import settings
import uuid


class WasteCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=10, blank=True)  # emoji
    description = models.TextField(blank=True)
    base_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'waste_categories'
        verbose_name_plural = 'Waste Categories'

    def __str__(self):
        return self.name


class WasteListing(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('pending_review', 'En attente de révision'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('sold', 'Vendu'),
        ('collected', 'Collecté'),
        ('archived', 'Archivé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='waste_listings')
    category = models.ForeignKey(WasteCategory, on_delete=models.SET_NULL, null=True, related_name='listings')

    # Informations de base
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quantity_kg = models.DecimalField(max_digits=8, decimal_places=2, help_text='Poids estimé en kg')

    # Photo
    photo = models.ImageField(upload_to='waste_photos/')
    photo_url = models.URLField(blank=True)  # URL Cloudinary

    # Analyse AI
    ai_analysis = models.JSONField(null=True, blank=True)
    # Structure : {
    #   "category": "Plastique PET",
    #   "recyclability_score": 8.5,
    #   "estimated_value_htg": 250.00,
    #   "estimated_value_usd": 1.85,
    #   "condition": "Bon état",
    #   "description": "Bouteilles en plastique PET...",
    #   "recommendations": "...",
    #   "confidence": 0.92
    # }
    ai_estimated_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ai_analyzed_at = models.DateTimeField(null=True, blank=True)

    # Localisation
    pickup_address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Statut
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_listings'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'waste_listings'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} — {self.user.full_name}'


class WastePhoto(models.Model):
    """Photos additionnelles pour un listing (galerie)"""
    listing = models.ForeignKey(WasteListing, on_delete=models.CASCADE, related_name='additional_photos')
    photo = models.ImageField(upload_to='waste_photos/gallery/')
    order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'waste_photos'
        ordering = ['order']
```

### apps/waste/ai_service.py

```python
"""
Service d'analyse AI des déchets via Claude Vision API (Anthropic).
Reçoit une image, retourne une analyse structurée.
"""
import anthropic
import base64
import json
from django.conf import settings
from pathlib import Path


ANALYSIS_PROMPT = """
Tu es un expert en recyclage et en valorisation des déchets en Haïti.
Analyse cette image d'un déchet et retourne UNIQUEMENT un objet JSON valide (sans markdown, sans backticks) avec cette structure exacte :

{
  "category": "Nom de la catégorie (ex: Plastique PET, Métal ferreux, Carton, Électronique, Verre, Pneu usagé, Autre)",
  "category_slug": "slug de la catégorie (plastic, metal, paper, electronics, glass, tires, other)",
  "recyclability_score": <nombre entre 0 et 10>,
  "condition": "Très bon / Bon / Moyen / Mauvais",
  "estimated_weight_kg": <estimation du poids en kg, un nombre>,
  "estimated_value_htg": <valeur estimée en Gourdes haïtiennes, un nombre>,
  "estimated_value_usd": <valeur estimée en USD, un nombre>,
  "description": "Description détaillée du déchet visible sur l'image",
  "recommendations": "Recommandations de traitement et de recyclage",
  "confidence": <niveau de confiance entre 0 et 1>,
  "is_recyclable": <true ou false>,
  "hazardous": <true si matière dangereuse, sinon false>
}

Si l'image ne montre pas clairement un déchet ou un matériau recyclable, retourne :
{"error": "Image non valide ou déchet non identifiable", "is_recyclable": false}

Adapte les valeurs économiques au contexte haïtien (marché local de recyclage).
"""


class WasteAIService:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def analyze_image_from_file(self, image_path: str) -> dict:
        """Analyser une image depuis un chemin de fichier."""
        with open(image_path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')
        ext = Path(image_path).suffix.lower()
        media_type_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}
        media_type = media_type_map.get(ext, 'image/jpeg')
        return self._call_claude(image_data, media_type)

    def analyze_image_from_base64(self, base64_data: str, media_type: str = 'image/jpeg') -> dict:
        """Analyser une image depuis des données base64."""
        # Supprimer le préfixe data URI si présent
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        return self._call_claude(base64_data, media_type)

    def analyze_image_from_url(self, url: str) -> dict:
        """Analyser une image depuis une URL Cloudinary."""
        import urllib.request
        import urllib.error
        try:
            with urllib.request.urlopen(url) as response:
                image_data = base64.standard_b64encode(response.read()).decode('utf-8')
                content_type = response.headers.get('Content-Type', 'image/jpeg')
                media_type = content_type.split(';')[0].strip()
            return self._call_claude(image_data, media_type)
        except urllib.error.URLError as e:
            return {'error': f'Impossible de charger l\'image: {str(e)}'}

    def _call_claude(self, image_data: str, media_type: str) -> dict:
        """Appel effectif à l'API Claude Vision."""
        try:
            message = self.client.messages.create(
                model='claude-opus-4-5',
                max_tokens=1024,
                messages=[
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'image',
                                'source': {
                                    'type': 'base64',
                                    'media_type': media_type,
                                    'data': image_data,
                                },
                            },
                            {
                                'type': 'text',
                                'text': ANALYSIS_PROMPT,
                            }
                        ],
                    }
                ],
            )
            raw_response = message.content[0].text.strip()
            # Nettoyer la réponse au cas où
            if raw_response.startswith('```'):
                raw_response = raw_response.split('```')[1]
                if raw_response.startswith('json'):
                    raw_response = raw_response[4:]
            return json.loads(raw_response)
        except json.JSONDecodeError:
            return {'error': 'Réponse AI non parseable', 'raw': raw_response}
        except Exception as e:
            return {'error': f'Erreur API Claude: {str(e)}'}


# Singleton
ai_service = WasteAIService()
```

### apps/waste/serializers.py

```python
from rest_framework import serializers
from .models import WasteListing, WasteCategory, WastePhoto


class WasteCategorySerializer(serializers.ModelSerializer):
    listing_count = serializers.SerializerMethodField()

    class Meta:
        model = WasteCategory
        fields = ['id', 'name', 'slug', 'icon', 'description', 'base_price_per_kg', 'listing_count']

    def get_listing_count(self, obj):
        return obj.listings.filter(status='approved').count()


class WastePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = WastePhoto
        fields = ['id', 'photo', 'order']


class WasteListingSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    user_name = serializers.ReadOnlyField(source='user.full_name')
    additional_photos = WastePhotoSerializer(many=True, read_only=True)

    class Meta:
        model = WasteListing
        fields = [
            'id', 'user', 'user_name', 'category', 'category_name',
            'title', 'description', 'quantity_kg', 'photo', 'photo_url',
            'ai_analysis', 'ai_estimated_value', 'ai_analyzed_at',
            'pickup_address', 'city', 'latitude', 'longitude',
            'status', 'rejection_reason',
            'additional_photos', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'user', 'ai_analysis', 'ai_estimated_value',
            'ai_analyzed_at', 'status', 'rejection_reason', 'created_at', 'updated_at'
        ]


class CreateWasteListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = WasteListing
        fields = ['title', 'description', 'category', 'quantity_kg', 'photo', 'pickup_address', 'city', 'latitude', 'longitude']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['status'] = 'pending_review'
        return super().create(validated_data)


class AIAnalysisRequestSerializer(serializers.Serializer):
    """Pour analyser une image sans créer un listing."""
    image_base64 = serializers.CharField(required=False)
    image_url = serializers.URLField(required=False)

    def validate(self, attrs):
        if not attrs.get('image_base64') and not attrs.get('image_url'):
            raise serializers.ValidationError('Fournir image_base64 ou image_url.')
        return attrs


class AdminReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs['action'] == 'reject' and not attrs.get('rejection_reason'):
            raise serializers.ValidationError({'rejection_reason': 'Raison de rejet requise.'})
        return attrs
```

### apps/waste/views.py

```python
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import WasteListing, WasteCategory
from .serializers import (
    WasteListingSerializer, CreateWasteListingSerializer,
    WasteCategorySerializer, AIAnalysisRequestSerializer, AdminReviewSerializer
)
from .ai_service import ai_service
from .tasks import analyze_waste_photo_async, notify_admin_new_listing
from apps.accounts.permissions import IsAdmin, IsOwnerOrAdmin


class WasteCategoryListView(generics.ListAPIView):
    """GET /api/waste/categories/"""
    serializer_class = WasteCategorySerializer
    permission_classes = [permissions.AllowAny]
    queryset = WasteCategory.objects.filter(is_active=True)


class WasteListingListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/waste/listings/         — Lister les listings de l'utilisateur connecté
    POST /api/waste/listings/         — Créer un nouveau listing
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateWasteListingSerializer
        return WasteListingSerializer

    def get_queryset(self):
        return WasteListing.objects.filter(user=self.request.user).select_related('category')

    def perform_create(self, serializer):
        listing = serializer.save()
        # Lancer l'analyse AI en arrière-plan
        analyze_waste_photo_async.delay(str(listing.id))
        # Notifier les admins
        notify_admin_new_listing.delay(str(listing.id))


class WasteListingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/waste/listings/<id>/"""
    serializer_class = WasteListingSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        return WasteListing.objects.select_related('category', 'user')


class AIAnalysisView(APIView):
    """
    POST /api/waste/analyze/
    Analyse une image via Claude Vision et retourne les résultats.
    Ne crée pas de listing — permet un preview avant soumission.
    """
    throttle_scope = 'ai_analysis'

    def post(self, request):
        serializer = AIAnalysisRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get('image_base64'):
            result = ai_service.analyze_image_from_base64(serializer.validated_data['image_base64'])
        else:
            result = ai_service.analyze_image_from_url(serializer.validated_data['image_url'])

        if 'error' in result:
            return Response({'error': result['error']}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        return Response({'analysis': result})


class AdminListingListView(generics.ListAPIView):
    """GET /api/waste/admin/listings/ — Tous les listings pour les admins"""
    serializer_class = WasteListingSerializer
    permission_classes = [IsAdmin]
    queryset = WasteListing.objects.select_related('category', 'user').all()
    filterset_fields = ['status', 'category', 'city']
    search_fields = ['title', 'user__email', 'user__first_name']
    ordering_fields = ['created_at', 'ai_estimated_value']


class AdminReviewListingView(APIView):
    """POST /api/waste/admin/listings/<id>/review/ — Approuver ou rejeter un listing"""
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        listing = get_object_or_404(WasteListing, pk=pk)
        serializer = AdminReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        listing.reviewed_by = request.user
        listing.reviewed_at = timezone.now()

        if action == 'approve':
            listing.status = 'approved'
            listing.save()
            # Notifier le user par email + push
            from apps.notifications.tasks import notify_listing_approved
            notify_listing_approved.delay(str(listing.id))
        else:
            listing.status = 'rejected'
            listing.rejection_reason = serializer.validated_data.get('rejection_reason', '')
            listing.save()
            from apps.notifications.tasks import notify_listing_rejected
            notify_listing_rejected.delay(str(listing.id))

        return Response(WasteListingSerializer(listing).data)
```

### apps/waste/tasks.py

```python
from celery import shared_task
from django.utils import timezone


@shared_task(name='waste.analyze_photo', bind=True, max_retries=3)
def analyze_waste_photo_async(self, listing_id: str):
    """Analyser la photo d'un listing via Claude Vision."""
    from .models import WasteListing
    from .ai_service import ai_service
    try:
        listing = WasteListing.objects.get(id=listing_id)
        if listing.photo:
            # Utiliser l'URL Cloudinary
            photo_url = listing.photo.url
            result = ai_service.analyze_image_from_url(photo_url)
            if 'error' not in result:
                listing.ai_analysis = result
                listing.ai_estimated_value = result.get('estimated_value_htg')
                listing.ai_analyzed_at = timezone.now()
                # Auto-remplir la catégorie si non définie
                if not listing.category and result.get('category_slug'):
                    from .models import WasteCategory
                    category = WasteCategory.objects.filter(slug=result['category_slug']).first()
                    if category:
                        listing.category = category
                listing.save()
    except WasteListing.DoesNotExist:
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task(name='waste.notify_admin_new_listing')
def notify_admin_new_listing(listing_id: str):
    """Notifier les admins d'un nouveau listing soumis."""
    from .models import WasteListing
    from apps.notifications.email_service import EmailService
    from apps.accounts.models import User
    try:
        listing = WasteListing.objects.select_related('user', 'category').get(id=listing_id)
        admins = User.objects.filter(role='admin', is_active=True)
        for admin in admins:
            EmailService.send_admin_new_listing(admin=admin, listing=listing)
    except WasteListing.DoesNotExist:
        pass
```

---

## 9. App — marketplace

### apps/marketplace/models.py

```python
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import uuid


class Auction(models.Model):
    TYPE_CHOICES = [
        ('auction', 'Enchère'),
        ('buy_now', 'Achat immédiat'),
        ('both', 'Enchère + Achat immédiat'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Clôturée'),
        ('sold', 'Vendue'),
        ('cancelled', 'Annulée'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.OneToOneField('waste.WasteListing', on_delete=models.CASCADE, related_name='auction')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='auctions')

    auction_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='both')
    starting_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    buy_now_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reserve_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()

    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='won_auctions'
    )
    total_bids = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'auctions'
        ordering = ['-created_at']

    def __str__(self):
        return f'Auction — {self.listing.title}'

    @property
    def current_bid(self):
        return self.current_price or self.starting_price

    @property
    def is_active(self):
        from django.utils import timezone
        return self.status == 'active' and self.ends_at > timezone.now()


class Bid(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_winning = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bids'
        ordering = ['-amount']

    def __str__(self):
        return f'{self.bidder.full_name} — {self.amount} HTG'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending_payment', 'En attente de paiement'),
        ('paid', 'Payé'),
        ('processing', 'En traitement'),
        ('pickup_scheduled', 'Ramassage planifié'),
        ('completed', 'Complété'),
        ('cancelled', 'Annulé'),
        ('refunded', 'Remboursé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auction = models.OneToOneField(Auction, on_delete=models.CASCADE, related_name='order')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sales')

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    seller_payout = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Calculer la commission plateforme (10%) et le payout vendeur
        self.platform_fee = self.amount * 0.10
        self.seller_payout = self.amount - self.platform_fee
        super().save(*args, **kwargs)
```

### apps/marketplace/serializers.py

```python
from rest_framework import serializers
from .models import Auction, Bid, Order
from apps.waste.serializers import WasteListingSerializer


class BidSerializer(serializers.ModelSerializer):
    bidder_name = serializers.ReadOnlyField(source='bidder.full_name')

    class Meta:
        model = Bid
        fields = ['id', 'bidder', 'bidder_name', 'amount', 'is_winning', 'created_at']
        read_only_fields = ['id', 'bidder', 'is_winning', 'created_at']


class AuctionSerializer(serializers.ModelSerializer):
    listing = WasteListingSerializer(read_only=True)
    seller_name = serializers.ReadOnlyField(source='seller.full_name')
    latest_bids = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    user_bid = serializers.SerializerMethodField()

    class Meta:
        model = Auction
        fields = [
            'id', 'listing', 'seller', 'seller_name',
            'auction_type', 'starting_price', 'buy_now_price',
            'current_price', 'reserve_price', 'status',
            'starts_at', 'ends_at', 'winner',
            'total_bids', 'views_count',
            'latest_bids', 'time_remaining', 'user_bid',
            'created_at',
        ]
        read_only_fields = ['id', 'seller', 'current_price', 'total_bids', 'views_count', 'winner']

    def get_latest_bids(self, obj):
        bids = obj.bids.order_by('-amount')[:5]
        return BidSerializer(bids, many=True).data

    def get_time_remaining(self, obj):
        from django.utils import timezone
        if obj.ends_at > timezone.now():
            delta = obj.ends_at - timezone.now()
            return int(delta.total_seconds())
        return 0

    def get_user_bid(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            bid = obj.bids.filter(bidder=request.user).order_by('-amount').first()
            if bid:
                return BidSerializer(bid).data
        return None


class CreateAuctionSerializer(serializers.ModelSerializer):
    listing_id = serializers.UUIDField()

    class Meta:
        model = Auction
        fields = ['listing_id', 'auction_type', 'starting_price', 'buy_now_price', 'reserve_price', 'starts_at', 'ends_at']

    def validate_listing_id(self, value):
        from apps.waste.models import WasteListing
        try:
            listing = WasteListing.objects.get(id=value, user=self.context['request'].user, status='approved')
            if hasattr(listing, 'auction'):
                raise serializers.ValidationError('Ce listing a déjà une enchère.')
            return value
        except WasteListing.DoesNotExist:
            raise serializers.ValidationError('Listing invalide ou non approuvé.')

    def create(self, validated_data):
        from apps.waste.models import WasteListing
        listing = WasteListing.objects.get(id=validated_data.pop('listing_id'))
        validated_data['seller'] = self.context['request'].user
        validated_data['listing'] = listing
        validated_data['current_price'] = validated_data['starting_price']
        return super().create(validated_data)


class PlaceBidSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_amount(self, value):
        auction = self.context.get('auction')
        if auction:
            min_bid = (auction.current_price or auction.starting_price) + 10
            if value < min_bid:
                raise serializers.ValidationError(f'L\'enchère minimale est {min_bid} HTG.')
        return value


class OrderSerializer(serializers.ModelSerializer):
    buyer_name = serializers.ReadOnlyField(source='buyer.full_name')
    seller_name = serializers.ReadOnlyField(source='seller.full_name')
    listing_title = serializers.ReadOnlyField(source='auction.listing.title')

    class Meta:
        model = Order
        fields = [
            'id', 'auction', 'buyer', 'buyer_name', 'seller', 'seller_name',
            'listing_title', 'amount', 'platform_fee', 'seller_payout',
            'status', 'notes', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['id', 'buyer', 'seller', 'platform_fee', 'seller_payout']
```

### apps/marketplace/views.py

```python
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Auction, Bid, Order
from .serializers import (
    AuctionSerializer, CreateAuctionSerializer,
    PlaceBidSerializer, OrderSerializer, BidSerializer
)
from apps.accounts.permissions import IsAdmin, IsOwnerOrAdmin


class PublicAuctionListView(generics.ListAPIView):
    """GET /api/marketplace/auctions/ — Auctions publiques"""
    serializer_class = AuctionSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['status', 'auction_type', 'listing__category']
    search_fields = ['listing__title', 'listing__description']
    ordering_fields = ['created_at', 'ends_at', 'current_price', 'total_bids']

    def get_queryset(self):
        return Auction.objects.filter(
            status='active',
            starts_at__lte=timezone.now()
        ).select_related('listing', 'listing__category', 'seller')


class AuctionDetailView(generics.RetrieveAPIView):
    """GET /api/marketplace/auctions/<id>/"""
    serializer_class = AuctionSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Auction.objects.select_related('listing', 'seller')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Incrémenter le compteur de vues
        Auction.objects.filter(pk=instance.pk).update(views_count=instance.views_count + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class CreateAuctionView(generics.CreateAPIView):
    """POST /api/marketplace/auctions/create/"""
    serializer_class = CreateAuctionSerializer


class PlaceBidView(APIView):
    """POST /api/marketplace/auctions/<id>/bid/"""
    def post(self, request, pk):
        auction = get_object_or_404(Auction, pk=pk)

        if not auction.is_active:
            return Response({'error': 'Cette enchère est clôturée.'}, status=status.HTTP_400_BAD_REQUEST)
        if auction.seller == request.user:
            return Response({'error': 'Vous ne pouvez pas enchérir sur votre propre listing.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PlaceBidSerializer(data=request.data, context={'auction': auction})
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data['amount']

        # Marquer l'ancienne enchère gagnante comme non gagnante
        auction.bids.filter(is_winning=True).update(is_winning=False)

        # Créer la nouvelle enchère
        bid = Bid.objects.create(auction=auction, bidder=request.user, amount=amount, is_winning=True)

        # Mettre à jour l'enchère courante
        auction.current_price = amount
        auction.total_bids += 1
        auction.save()

        # Notifier le vendeur + l'ancien leader
        from apps.notifications.tasks import notify_new_bid
        notify_new_bid.delay(str(bid.id))

        return Response(BidSerializer(bid).data, status=status.HTTP_201_CREATED)


class BuyNowView(APIView):
    """POST /api/marketplace/auctions/<id>/buy-now/"""
    def post(self, request, pk):
        auction = get_object_or_404(Auction, pk=pk)

        if not auction.is_active:
            return Response({'error': 'Cette enchère n\'est plus disponible.'}, status=status.HTTP_400_BAD_REQUEST)
        if not auction.buy_now_price:
            return Response({'error': 'Achat immédiat non disponible.'}, status=status.HTTP_400_BAD_REQUEST)
        if auction.seller == request.user:
            return Response({'error': 'Vous ne pouvez pas acheter votre propre listing.'}, status=status.HTTP_400_BAD_REQUEST)

        # Clôturer l'enchère et créer la commande
        auction.status = 'sold'
        auction.winner = request.user
        auction.save()

        order = Order.objects.create(
            auction=auction,
            buyer=request.user,
            seller=auction.seller,
            amount=auction.buy_now_price,
        )

        # Notifier + créer impact record
        from apps.notifications.tasks import notify_order_created
        from apps.impact.tasks import create_impact_record
        notify_order_created.delay(str(order.id))
        create_impact_record.delay(str(order.id))

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class MyOrdersView(generics.ListAPIView):
    """GET /api/marketplace/orders/my/ — Commandes de l'utilisateur"""
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user).select_related('auction', 'seller')


class MySalesView(generics.ListAPIView):
    """GET /api/marketplace/orders/sales/ — Ventes de l'utilisateur"""
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(seller=self.request.user).select_related('auction', 'buyer')


class AdminOrderListView(generics.ListAPIView):
    """GET /api/marketplace/admin/orders/"""
    serializer_class = OrderSerializer
    permission_classes = [IsAdmin]
    queryset = Order.objects.select_related('auction', 'buyer', 'seller').all()
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'amount']
```

### apps/marketplace/tasks.py

```python
from celery import shared_task


@shared_task(name='marketplace.close_expired_auctions')
def close_expired_auctions():
    """Clôturer automatiquement les enchères expirées."""
    from django.utils import timezone
    from .models import Auction, Order
    from apps.notifications.tasks import notify_auction_closed

    expired = Auction.objects.filter(status='active', ends_at__lte=timezone.now())
    for auction in expired:
        winning_bid = auction.bids.filter(is_winning=True).first()
        if winning_bid:
            auction.status = 'sold'
            auction.winner = winning_bid.bidder
            auction.save()
            # Créer la commande
            order = Order.objects.create(
                auction=auction,
                buyer=winning_bid.bidder,
                seller=auction.seller,
                amount=winning_bid.amount,
            )
            notify_auction_closed.delay(str(auction.id), winner=True)
            from apps.impact.tasks import create_impact_record
            create_impact_record.delay(str(order.id))
        else:
            auction.status = 'closed'
            auction.save()
            notify_auction_closed.delay(str(auction.id), winner=False)
```

---

## 10. App — collections

### apps/collections/models.py

```python
from django.db import models
from django.conf import settings
import uuid


class PickupRequest(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Demandé'),
        ('assigned', 'Assigné'),
        ('in_transit', 'En transit'),
        ('arrived', 'Arrivé'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
    ]

    SLOT_CHOICES = [
        ('morning', 'Matin (8h-12h)'),
        ('afternoon', 'Après-midi (12h-17h)'),
        ('evening', 'Soir (17h-20h)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pickup_requests')
    listing = models.ForeignKey('waste.WasteListing', on_delete=models.CASCADE, related_name='pickup_requests', null=True, blank=True)
    collector = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_pickups'
    )

    # Adresse et créneau
    address = models.TextField()
    city = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    preferred_date = models.DateField()
    preferred_slot = models.CharField(max_length=20, choices=SLOT_CHOICES)
    special_instructions = models.TextField(blank=True)

    # Statut
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    status_history = models.JSONField(default=list)
    # Structure: [{"status": "requested", "timestamp": "...", "note": "..."}]

    # Résultat
    actual_weight_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    collector_notes = models.TextField(blank=True)
    completion_photo = models.ImageField(upload_to='pickups/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'pickup_requests'
        ordering = ['-created_at']

    def update_status(self, new_status, note=''):
        from django.utils import timezone
        self.status = new_status
        self.status_history.append({
            'status': new_status,
            'timestamp': timezone.now().isoformat(),
            'note': note,
        })
        if new_status == 'completed':
            self.completed_at = timezone.now()
        self.save()
```

### apps/collections/views.py

```python
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import PickupRequest
from .serializers import PickupRequestSerializer, CreatePickupRequestSerializer, AssignCollectorSerializer, UpdateStatusSerializer
from apps.accounts.permissions import IsAdmin, IsCollector, IsOwnerOrAdmin


class PickupRequestListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/collections/         — Mes demandes de ramassage
    POST /api/collections/         — Créer une demande
    """
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreatePickupRequestSerializer
        return PickupRequestSerializer

    def get_queryset(self):
        return PickupRequest.objects.filter(user=self.request.user).select_related('collector', 'listing')

    def perform_create(self, serializer):
        pickup = serializer.save(user=self.request.user)
        from apps.notifications.tasks import notify_admin_new_pickup
        notify_admin_new_pickup.delay(str(pickup.id))


class PickupRequestDetailView(generics.RetrieveAPIView):
    """GET /api/collections/<id>/"""
    serializer_class = PickupRequestSerializer
    permission_classes = [IsOwnerOrAdmin]
    queryset = PickupRequest.objects.select_related('collector', 'listing', 'user')


class AdminPickupListView(generics.ListAPIView):
    """GET /api/collections/admin/ — Toutes les demandes (admin)"""
    serializer_class = PickupRequestSerializer
    permission_classes = [IsAdmin]
    queryset = PickupRequest.objects.select_related('user', 'collector', 'listing').all()
    filterset_fields = ['status', 'city', 'preferred_date']


class AssignCollectorView(APIView):
    """POST /api/collections/<id>/assign/ — Assigner un ramasseur (admin)"""
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        pickup = get_object_or_404(PickupRequest, pk=pk)
        serializer = AssignCollectorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        collector = serializer.validated_data['collector']
        pickup.collector = collector
        pickup.update_status('assigned', f'Assigné à {collector.full_name}')
        # Notifier le collecteur via FCM
        from apps.notifications.tasks import notify_collector_assigned
        notify_collector_assigned.delay(str(pickup.id))
        return Response(PickupRequestSerializer(pickup).data)


class CollectorPickupListView(generics.ListAPIView):
    """GET /api/collections/collector/ — Ramassages assignés au collecteur"""
    serializer_class = PickupRequestSerializer
    permission_classes = [IsCollector]

    def get_queryset(self):
        return PickupRequest.objects.filter(
            collector=self.request.user,
            status__in=['assigned', 'in_transit', 'arrived']
        ).select_related('user', 'listing')


class UpdatePickupStatusView(APIView):
    """POST /api/collections/<id>/status/ — Mettre à jour le statut (collecteur/admin)"""
    permission_classes = [IsCollector]

    def post(self, request, pk):
        pickup = get_object_or_404(PickupRequest, pk=pk, collector=request.user)
        serializer = UpdateStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pickup.update_status(
            serializer.validated_data['status'],
            serializer.validated_data.get('note', '')
        )
        if serializer.validated_data.get('actual_weight_kg'):
            pickup.actual_weight_kg = serializer.validated_data['actual_weight_kg']
            pickup.save()
        # Notifier le user
        from apps.notifications.tasks import notify_pickup_status_update
        notify_pickup_status_update.delay(str(pickup.id))
        return Response(PickupRequestSerializer(pickup).data)
```

---

## 11. App — notifications

### apps/notifications/models.py

```python
from django.db import models
from django.conf import settings
import uuid


class Notification(models.Model):
    TYPE_CHOICES = [
        ('listing_approved', 'Listing approuvé'),
        ('listing_rejected', 'Listing rejeté'),
        ('new_bid', 'Nouvelle enchère'),
        ('auction_won', 'Enchère gagnée'),
        ('auction_lost', 'Enchère perdue'),
        ('auction_closed', 'Enchère clôturée'),
        ('order_created', 'Commande créée'),
        ('pickup_assigned', 'Ramassage assigné'),
        ('pickup_status', 'Statut ramassage'),
        ('pickup_completed', 'Ramassage complété'),
        ('new_listing_admin', 'Nouveau listing (admin)'),
        ('system', 'Système'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict)  # données additionnelles (listing_id, order_id, etc.)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
```

### apps/notifications/email_service.py

```python
"""
Service d'envoi d'emails via Resend API.
"""
import resend
from django.conf import settings
from django.template.loader import render_to_string


resend.api_key = settings.RESEND_API_KEY


class EmailService:

    @staticmethod
    def _send(to: str, subject: str, html: str):
        """Méthode interne d'envoi."""
        try:
            resend.Emails.send({
                'from': f'{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>',
                'to': [to],
                'subject': subject,
                'html': html,
            })
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'Email send error: {e}')

    @classmethod
    def send_welcome(cls, user, verify_url: str):
        html = render_to_string('emails/welcome.html', {
            'user': user,
            'verify_url': verify_url,
            'frontend_url': settings.FRONTEND_URL,
        })
        cls._send(user.email, '🌱 Bienvenue sur EcoCycle Haiti !', html)

    @classmethod
    def send_verification(cls, user, verify_url: str):
        html = render_to_string('emails/verify_email.html', {
            'user': user,
            'verify_url': verify_url,
        })
        cls._send(user.email, '✅ Vérifiez votre adresse email — EcoCycle', html)

    @classmethod
    def send_password_reset(cls, user, reset_url: str):
        html = render_to_string('emails/reset_password.html', {
            'user': user,
            'reset_url': reset_url,
        })
        cls._send(user.email, '🔐 Réinitialisation de votre mot de passe — EcoCycle', html)

    @classmethod
    def send_listing_approved(cls, listing):
        from django.conf import settings as django_settings
        html = render_to_string('emails/listing_approved.html', {
            'user': listing.user,
            'listing': listing,
            'marketplace_url': f'{django_settings.FRONTEND_URL}/marketplace',
        })
        cls._send(
            listing.user.email,
            '♻️ Votre listing a été approuvé — EcoCycle',
            html
        )

    @classmethod
    def send_listing_rejected(cls, listing):
        html = render_to_string('emails/listing_approved.html', {
            'user': listing.user,
            'listing': listing,
            'reason': listing.rejection_reason,
        })
        cls._send(listing.user.email, '❌ Votre listing n\'a pas été approuvé — EcoCycle', html)

    @classmethod
    def send_auction_won(cls, order):
        html = render_to_string('emails/auction_won.html', {
            'user': order.buyer,
            'order': order,
            'listing': order.auction.listing,
            'frontend_url': settings.FRONTEND_URL,
        })
        cls._send(order.buyer.email, '🎉 Vous avez remporté l\'enchère ! — EcoCycle', html)

    @classmethod
    def send_pickup_confirmed(cls, pickup):
        html = render_to_string('emails/pickup_confirmed.html', {
            'user': pickup.user,
            'pickup': pickup,
        })
        cls._send(pickup.user.email, '🚚 Votre ramassage est confirmé — EcoCycle', html)

    @classmethod
    def send_admin_new_listing(cls, admin, listing):
        html = render_to_string('emails/listing_approved.html', {
            'admin': admin,
            'listing': listing,
            'review_url': f'{settings.FRONTEND_URL}/admin/listings/{listing.id}',
        })
        cls._send(admin.email, f'[EcoCycle Admin] Nouveau listing à réviser : {listing.title}', html)

    @classmethod
    def send_newsletter_confirmation(cls, subscriber):
        html = render_to_string('emails/newsletter_confirm.html', {
            'subscriber': subscriber,
            'confirm_url': f'{settings.FRONTEND_URL}/newsletter/confirm/{subscriber.token}',
        })
        cls._send(subscriber.email, '📧 Confirmez votre abonnement — EcoCycle', html)
```

### apps/notifications/fcm_service.py

```python
"""
Service de push notifications via Firebase Cloud Messaging (FCM).
Utilise firebase-admin SDK.
"""
import json
import base64
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings


def _initialize_firebase():
    if not firebase_admin._apps:
        if settings.FIREBASE_CREDENTIALS_B64:
            # Décoder depuis variable d'environnement (Railway)
            creds_json = json.loads(base64.b64decode(settings.FIREBASE_CREDENTIALS_B64).decode())
            cred = credentials.Certificate(creds_json)
        else:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)


_initialize_firebase()


class FCMService:

    @staticmethod
    def send_to_user(user, title: str, body: str, data: dict = None):
        """Envoyer une notification à un utilisateur via son FCM token."""
        if not user.fcm_token:
            return None
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={str(k): str(v) for k, v in (data or {}).items()},
                token=user.fcm_token,
                android=messaging.AndroidConfig(priority='high'),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(sound='default')
                    )
                ),
            )
            return messaging.send(message)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'FCM send error: {e}')
            return None

    @staticmethod
    def send_to_multiple(users, title: str, body: str, data: dict = None):
        """Envoyer à plusieurs utilisateurs."""
        tokens = [u.fcm_token for u in users if u.fcm_token]
        if not tokens:
            return
        try:
            multicast = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data={str(k): str(v) for k, v in (data or {}).items()},
                tokens=tokens,
            )
            return messaging.send_each_for_multicast(multicast)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'FCM multicast error: {e}')
```

### apps/notifications/tasks.py

```python
from celery import shared_task
from .models import Notification


def _create_notification(user, notif_type, title, message, data=None):
    Notification.objects.create(
        user=user, notification_type=notif_type,
        title=title, message=message, data=data or {}
    )


@shared_task(name='notifications.notify_listing_approved')
def notify_listing_approved(listing_id: str):
    from apps.waste.models import WasteListing
    from .email_service import EmailService
    from .fcm_service import FCMService
    listing = WasteListing.objects.select_related('user').get(id=listing_id)
    _create_notification(
        listing.user, 'listing_approved',
        '♻️ Listing approuvé',
        f'Votre listing "{listing.title}" a été approuvé et est maintenant sur la marketplace.',
        {'listing_id': str(listing.id)}
    )
    EmailService.send_listing_approved(listing)
    FCMService.send_to_user(
        listing.user,
        '♻️ Listing approuvé !',
        f'"{listing.title}" est maintenant en ligne sur la marketplace.',
        {'type': 'listing_approved', 'listing_id': str(listing.id)}
    )


@shared_task(name='notifications.notify_listing_rejected')
def notify_listing_rejected(listing_id: str):
    from apps.waste.models import WasteListing
    from .email_service import EmailService
    from .fcm_service import FCMService
    listing = WasteListing.objects.select_related('user').get(id=listing_id)
    _create_notification(
        listing.user, 'listing_rejected',
        '❌ Listing non approuvé',
        f'Votre listing "{listing.title}" n\'a pas été approuvé. Raison: {listing.rejection_reason}',
        {'listing_id': str(listing.id)}
    )
    EmailService.send_listing_rejected(listing)
    FCMService.send_to_user(
        listing.user,
        '❌ Listing non approuvé',
        f'Voir les détails pour "{listing.title}".',
        {'type': 'listing_rejected', 'listing_id': str(listing.id)}
    )


@shared_task(name='notifications.notify_new_bid')
def notify_new_bid(bid_id: str):
    from apps.marketplace.models import Bid
    from .fcm_service import FCMService
    bid = Bid.objects.select_related('auction', 'auction__seller', 'bidder').get(id=bid_id)
    auction = bid.auction
    # Notifier le vendeur
    FCMService.send_to_user(
        auction.seller,
        '💰 Nouvelle enchère !',
        f'{bid.bidder.full_name} a enchéri {bid.amount} HTG sur "{auction.listing.title}".',
        {'type': 'new_bid', 'auction_id': str(auction.id)}
    )
    _create_notification(
        auction.seller, 'new_bid',
        '💰 Nouvelle enchère',
        f'{bid.bidder.full_name} — {bid.amount} HTG',
        {'auction_id': str(auction.id), 'bid_id': str(bid.id)}
    )


@shared_task(name='notifications.notify_auction_closed')
def notify_auction_closed(auction_id: str, winner: bool):
    from apps.marketplace.models import Auction
    from .email_service import EmailService
    from .fcm_service import FCMService
    auction = Auction.objects.select_related('winner', 'seller', 'listing').get(id=auction_id)
    if winner and auction.winner:
        # Notifier le gagnant
        FCMService.send_to_user(
            auction.winner, '🎉 Vous avez gagné !',
            f'Vous avez remporté l\'enchère pour "{auction.listing.title}" — {auction.current_price} HTG.',
            {'type': 'auction_won', 'auction_id': str(auction_id)}
        )
        if hasattr(auction, 'order'):
            EmailService.send_auction_won(auction.order)


@shared_task(name='notifications.notify_order_created')
def notify_order_created(order_id: str):
    from apps.marketplace.models import Order
    from .email_service import EmailService
    from .fcm_service import FCMService
    order = Order.objects.select_related('buyer', 'seller', 'auction__listing').get(id=order_id)
    _create_notification(
        order.buyer, 'order_created',
        '🛒 Commande confirmée',
        f'Votre achat de "{order.auction.listing.title}" est confirmé — {order.amount} HTG.',
        {'order_id': str(order.id)}
    )
    FCMService.send_to_user(
        order.buyer, '🛒 Commande confirmée',
        f'"{order.auction.listing.title}" — {order.amount} HTG.',
        {'type': 'order_created', 'order_id': str(order.id)}
    )


@shared_task(name='notifications.notify_admin_new_pickup')
def notify_admin_new_pickup(pickup_id: str):
    from apps.collections.models import PickupRequest
    from apps.accounts.models import User
    from .email_service import EmailService
    from .fcm_service import FCMService
    pickup = PickupRequest.objects.select_related('user').get(id=pickup_id)
    admins = User.objects.filter(role='admin', is_active=True)
    FCMService.send_to_multiple(
        list(admins),
        '🚚 Nouvelle demande de ramassage',
        f'{pickup.user.full_name} — {pickup.city}, {pickup.preferred_date}',
        {'type': 'new_pickup', 'pickup_id': str(pickup_id)}
    )


@shared_task(name='notifications.notify_collector_assigned')
def notify_collector_assigned(pickup_id: str):
    from apps.collections.models import PickupRequest
    from .fcm_service import FCMService
    from .email_service import EmailService
    pickup = PickupRequest.objects.select_related('collector', 'user').get(id=pickup_id)
    if pickup.collector:
        FCMService.send_to_user(
            pickup.collector,
            '🚚 Nouveau ramassage assigné',
            f'Ramassage chez {pickup.user.full_name} — {pickup.city}, {pickup.preferred_date}',
            {'type': 'pickup_assigned', 'pickup_id': str(pickup_id)}
        )
    # Notifier aussi l'utilisateur
    FCMService.send_to_user(
        pickup.user,
        '✅ Ramassage confirmé',
        f'Un collecteur a été assigné à votre demande du {pickup.preferred_date}.',
        {'type': 'pickup_confirmed', 'pickup_id': str(pickup_id)}
    )
    EmailService.send_pickup_confirmed(pickup)


@shared_task(name='notifications.notify_pickup_status_update')
def notify_pickup_status_update(pickup_id: str):
    from apps.collections.models import PickupRequest
    from .fcm_service import FCMService
    pickup = PickupRequest.objects.select_related('user').get(id=pickup_id)
    status_labels = {
        'in_transit': '🚛 Le collecteur est en route !',
        'arrived': '📍 Le collecteur est arrivé',
        'completed': '✅ Ramassage complété !',
        'failed': '❌ Ramassage échoué',
    }
    title = status_labels.get(pickup.status, '📦 Mise à jour du ramassage')
    FCMService.send_to_user(
        pickup.user, title,
        f'Ramassage du {pickup.preferred_date} — {pickup.get_status_display()}',
        {'type': 'pickup_status', 'pickup_id': str(pickup_id), 'status': pickup.status}
    )
    _create_notification(
        pickup.user, 'pickup_status', title,
        pickup.get_status_display(),
        {'pickup_id': str(pickup_id)}
    )
```

### apps/notifications/views.py

```python
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    """GET /api/notifications/ — Notifications de l'utilisateur"""
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class MarkNotificationReadView(APIView):
    """POST /api/notifications/<id>/read/"""
    def post(self, request, pk):
        notif = Notification.objects.filter(pk=pk, user=request.user).first()
        if notif:
            notif.is_read = True
            notif.save()
        return Response({'status': 'ok'})


class MarkAllReadView(APIView):
    """POST /api/notifications/read-all/"""
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'ok'})


class UnreadCountView(APIView):
    """GET /api/notifications/unread-count/"""
    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})
```

---

## 12. App — impact

### apps/impact/models.py

```python
from django.db import models
from django.conf import settings
import uuid

# Facteurs de conversion CO₂ par catégorie (kg CO₂ économisé par kg recyclé)
CO2_FACTORS = {
    'plastic': 1.5,
    'metal': 4.0,
    'paper': 0.9,
    'electronics': 20.0,
    'glass': 0.3,
    'tires': 2.8,
    'other': 0.5,
}


class ImpactRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='impact_records')
    order = models.OneToOneField('marketplace.Order', on_delete=models.CASCADE, related_name='impact', null=True, blank=True)
    pickup = models.OneToOneField('collections.PickupRequest', on_delete=models.CASCADE, related_name='impact', null=True, blank=True)

    category_slug = models.CharField(max_length=50, blank=True)
    kg_recycled = models.DecimalField(max_digits=8, decimal_places=2)
    co2_saved_kg = models.DecimalField(max_digits=10, decimal_places=3)
    economic_value_htg = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'impact_records'
        ordering = ['-created_at']


class UserImpactSummary(models.Model):
    """Vue agrégée de l'impact — mise à jour via signal."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='impact_summary')
    total_kg_recycled = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_co2_saved_kg = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    total_economic_value_htg = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_transactions = models.PositiveIntegerField(default=0)
    community_rank = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_impact_summaries'
```

### apps/impact/tasks.py

```python
from celery import shared_task


@shared_task(name='impact.create_impact_record')
def create_impact_record(order_id: str):
    from apps.marketplace.models import Order
    from .models import ImpactRecord, UserImpactSummary, CO2_FACTORS
    from django.db.models import Sum

    order = Order.objects.select_related(
        'buyer', 'auction__listing__category'
    ).get(id=order_id)

    listing = order.auction.listing
    category_slug = listing.category.slug if listing.category else 'other'
    kg = float(listing.quantity_kg or 1.0)
    co2 = kg * CO2_FACTORS.get(category_slug, 0.5)

    ImpactRecord.objects.create(
        user=order.buyer,
        order=order,
        category_slug=category_slug,
        kg_recycled=kg,
        co2_saved_kg=co2,
        economic_value_htg=order.amount,
    )

    # Mettre à jour le résumé
    summary, _ = UserImpactSummary.objects.get_or_create(user=order.buyer)
    records = ImpactRecord.objects.filter(user=order.buyer)
    agg = records.aggregate(
        total_kg=Sum('kg_recycled'),
        total_co2=Sum('co2_saved_kg'),
        total_value=Sum('economic_value_htg'),
    )
    summary.total_kg_recycled = agg['total_kg'] or 0
    summary.total_co2_saved_kg = agg['total_co2'] or 0
    summary.total_economic_value_htg = agg['total_value'] or 0
    summary.total_transactions = records.count()
    summary.save()

    # Recalculer les classements
    update_community_rankings.delay()


@shared_task(name='impact.update_community_rankings')
def update_community_rankings():
    from .models import UserImpactSummary
    summaries = UserImpactSummary.objects.order_by('-total_kg_recycled')
    for rank, summary in enumerate(summaries, start=1):
        UserImpactSummary.objects.filter(pk=summary.pk).update(community_rank=rank)
```

### apps/impact/views.py

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from django.db.models import Sum
from .models import ImpactRecord, UserImpactSummary
from .serializers import ImpactRecordSerializer, UserImpactSummarySerializer


class MyImpactDashboardView(APIView):
    """GET /api/impact/dashboard/ — Tableau de bord personnel"""
    def get(self, request):
        summary, _ = UserImpactSummary.objects.get_or_create(user=request.user)
        records = ImpactRecord.objects.filter(user=request.user).order_by('-created_at')[:10]
        return Response({
            'summary': UserImpactSummarySerializer(summary).data,
            'recent_records': ImpactRecordSerializer(records, many=True).data,
        })


class LeaderboardView(APIView):
    """GET /api/impact/leaderboard/ — Top recycleurs"""
    def get(self, request):
        top = UserImpactSummary.objects.select_related('user').order_by('-total_kg_recycled')[:20]
        return Response(UserImpactSummarySerializer(top, many=True).data)


class PublicStatsView(APIView):
    """GET /api/impact/stats/ — Stats globales (pour le hero de la landing)"""
    permission_classes = []

    def get(self, request):
        from apps.accounts.models import User
        from apps.marketplace.models import Order
        from apps.collections.models import PickupRequest
        agg = ImpactRecord.objects.aggregate(
            total_kg=Sum('kg_recycled'),
            total_co2=Sum('co2_saved_kg'),
        )
        return Response({
            'total_kg_recycled': agg['total_kg'] or 0,
            'total_co2_saved_kg': agg['total_co2'] or 0,
            'total_users': User.objects.filter(is_active=True).count(),
            'total_orders': Order.objects.filter(status='completed').count(),
            'total_pickups': PickupRequest.objects.filter(status='completed').count(),
        })
```

---

## 13. App — academy

### apps/academy/models.py

```python
from django.db import models
from django.conf import settings
from django.utils.text import slugify
import uuid


class Course(models.Model):
    LEVEL_CHOICES = [('beginner', 'Débutant'), ('intermediate', 'Intermédiaire'), ('advanced', 'Avancé')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='courses/', blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    duration_minutes = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    is_free = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'courses'
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Lesson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField()
    video_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    duration_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'lessons'
        ordering = ['order']


class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    completed_lessons = models.ManyToManyField(Lesson, blank=True)
    progress_percent = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'enrollments'
        unique_together = ['user', 'course']


class Certificate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'certificates'
        unique_together = ['user', 'course']
```

---

## 14. App — blog

### apps/blog/models.py

```python
from django.db import models
from django.conf import settings
from django.utils.text import slugify
import uuid


class BlogCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)


class Post(models.Model):
    STATUS_CHOICES = [('draft', 'Brouillon'), ('published', 'Publié')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, related_name='posts')
    title = models.CharField(max_length=300)
    slug = models.SlugField(unique=True, blank=True)
    excerpt = models.TextField(max_length=500)
    content = models.TextField()
    cover_image = models.ImageField(upload_to='blog/', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    read_time_minutes = models.PositiveIntegerField(default=5)
    views = models.PositiveIntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blog_posts'
        ordering = ['-published_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
```

---

## 15. App — core

### apps/core/models.py

```python
from django.db import models
import uuid


class ContactMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    replied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'contact_messages'
        ordering = ['-created_at']


class NewsletterSubscriber(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_confirmed = models.BooleanField(default=False)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'newsletter_subscribers'
```

### apps/core/views.py

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from .models import ContactMessage, NewsletterSubscriber
from .serializers import ContactMessageSerializer, NewsletterSerializer


class ContactView(APIView):
    """POST /api/contact/"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        # Notifier les admins
        from apps.notifications.email_service import EmailService
        from apps.accounts.models import User
        admins = User.objects.filter(role='admin')
        for admin in admins:
            EmailService._send(
                admin.email,
                f'[EcoCycle Contact] {message.subject}',
                f'<p>De : {message.first_name} {message.last_name} ({message.email})</p><p>{message.message}</p>'
            )
        return Response({'message': 'Message envoyé avec succès.'}, status=status.HTTP_201_CREATED)


class NewsletterSubscribeView(APIView):
    """POST /api/newsletter/subscribe/"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = NewsletterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
        if created or not subscriber.is_confirmed:
            from apps.notifications.email_service import EmailService
            EmailService.send_newsletter_confirmation(subscriber)
        return Response({'message': 'Vérifiez votre email pour confirmer l\'abonnement.'})


class NewsletterConfirmView(APIView):
    """GET /api/newsletter/confirm/<token>/"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        subscriber = get_object_or_404(NewsletterSubscriber, token=token)
        subscriber.is_confirmed = True
        subscriber.save()
        return Response({'message': 'Abonnement confirmé !'})
```

---

## 16. Services externes

### Résumé des intégrations

| Service | Usage | Déclenchement |
|---|---|---|
| **Claude Vision** | Analyse photo déchet | `POST /api/waste/analyze/` + tâche Celery post-upload |
| **Resend** | Emails transactionnels | Via `EmailService` dans tâches Celery |
| **Firebase FCM** | Push notifications Flutter | Via `FCMService` dans tâches Celery |
| **Cloudinary** | Stockage photos déchets + avatars | Auto via `DEFAULT_FILE_STORAGE` |
| **PostgreSQL** | Base de données principale | `dj-database-url` + `DATABASE_URL` Railway |
| **Redis** | Broker Celery + Cache Django | `REDIS_URL` Railway |

---

## 17. URLs globales

### config/urls.py

```python
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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### Tableau récapitulatif des endpoints API

```
AUTH
POST   /api/auth/register/
POST   /api/auth/login/
POST   /api/auth/logout/
POST   /api/auth/token/refresh/
GET    /api/auth/verify-email/<token>/
GET    /api/auth/profile/
PUT    /api/auth/profile/
POST   /api/auth/change-password/
POST   /api/auth/fcm-token/
POST   /api/auth/reset-password/
POST   /api/auth/reset-password/confirm/

WASTE
GET    /api/waste/categories/
GET    /api/waste/listings/
POST   /api/waste/listings/
GET    /api/waste/listings/<id>/
PUT    /api/waste/listings/<id>/
DELETE /api/waste/listings/<id>/
POST   /api/waste/analyze/                  ← Claude Vision AI
GET    /api/waste/admin/listings/           ← Admin
POST   /api/waste/admin/listings/<id>/review/  ← Admin

MARKETPLACE
GET    /api/marketplace/auctions/
GET    /api/marketplace/auctions/<id>/
POST   /api/marketplace/auctions/create/
POST   /api/marketplace/auctions/<id>/bid/
POST   /api/marketplace/auctions/<id>/buy-now/
GET    /api/marketplace/orders/my/
GET    /api/marketplace/orders/sales/
GET    /api/marketplace/admin/orders/      ← Admin

COLLECTIONS
GET    /api/collections/
POST   /api/collections/
GET    /api/collections/<id>/
GET    /api/collections/admin/             ← Admin
POST   /api/collections/<id>/assign/       ← Admin
GET    /api/collections/collector/         ← Collecteur
POST   /api/collections/<id>/status/       ← Collecteur

NOTIFICATIONS
GET    /api/notifications/
POST   /api/notifications/<id>/read/
POST   /api/notifications/read-all/
GET    /api/notifications/unread-count/

IMPACT
GET    /api/impact/dashboard/
GET    /api/impact/leaderboard/
GET    /api/impact/stats/                  ← Public

ACADEMY
GET    /api/academy/courses/
GET    /api/academy/courses/<slug>/
POST   /api/academy/courses/<slug>/enroll/
POST   /api/academy/lessons/<id>/complete/
GET    /api/academy/my-enrollments/
GET    /api/academy/my-certificates/

BLOG
GET    /api/blog/posts/
GET    /api/blog/posts/<slug>/

CORE
POST   /api/contact/
POST   /api/newsletter/subscribe/
GET    /api/newsletter/confirm/<token>/
```

---

## 18. Déploiement Railway

### Procfile

```
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
worker: celery -A config worker --loglevel=info --concurrency=2
beat: celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### railway.toml

```toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate"

[deploy]
startCommand = "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[[services]]
name = "web"

[[services]]
name = "celery-worker"
startCommand = "celery -A config worker --loglevel=info --concurrency=2"

[[services]]
name = "postgres"

[[services]]
name = "redis"
```

> **Note Railway :** Les variables `DATABASE_URL` et `REDIS_URL` sont injectées **automatiquement** par Railway quand tu connectes les plugins PostgreSQL et Redis à ton projet. Tu n'as pas à les définir manuellement.

### Variables d'environnement Railway à configurer manuellement

```
SECRET_KEY
DJANGO_SETTINGS_MODULE=config.settings.production
ALLOWED_HOSTS=your-app.railway.app
DEBUG=False
CLOUDINARY_CLOUD_NAME
CLOUDINARY_API_KEY
CLOUDINARY_API_SECRET
RESEND_API_KEY
RESEND_FROM_EMAIL
RESEND_FROM_NAME
ANTHROPIC_API_KEY
FIREBASE_CREDENTIALS_B64      ← credentials Firebase encodées en base64
FRONTEND_URL
ADMIN_EMAIL
CORS_ALLOWED_ORIGINS
```

### Encoder les credentials Firebase pour Railway

```bash
# Sur ta machine locale :
base64 -i firebase-credentials.json | tr -d '\n'
# Coller la valeur dans la variable FIREBASE_CREDENTIALS_B64 sur Railway
```

---

## 19. Commandes de setup

```bash
# 1. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OU
venv\Scripts\activate     # Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer l'environnement
cp .env.example .env
# Éditer .env avec tes valeurs

# 4. Créer les migrations
python manage.py makemigrations accounts
python manage.py makemigrations waste
python manage.py makemigrations marketplace
python manage.py makemigrations collections
python manage.py makemigrations notifications
python manage.py makemigrations impact
python manage.py makemigrations academy
python manage.py makemigrations blog
python manage.py makemigrations core

# 5. Appliquer les migrations
python manage.py migrate

# 6. Créer les catégories de déchets initiales
python manage.py shell -c "
from apps.waste.models import WasteCategory
categories = [
    ('Plastique', 'plastic', '🧴', 50),
    ('Métal', 'metal', '🔩', 120),
    ('Papier/Carton', 'paper', '📦', 30),
    ('Électronique', 'electronics', '💻', 500),
    ('Verre', 'glass', '🍶', 20),
    ('Pneus', 'tires', '🛞', 80),
    ('Autre', 'other', '♻️', 10),
]
for name, slug, icon, price in categories:
    WasteCategory.objects.get_or_create(slug=slug, defaults={
        'name': name, 'icon': icon, 'base_price_per_kg': price
    })
print('Catégories créées.')
"

# 7. Créer un superuser
python manage.py createsuperuser

# 8. Lancer le serveur de développement
python manage.py runserver

# 9. Dans un autre terminal : lancer Celery
celery -A config worker --loglevel=info

# 10. Dans un autre terminal : lancer Celery Beat (tâches périodiques)
celery -A config beat --loglevel=info

# 11. Collecter les fichiers statiques (production)
python manage.py collectstatic --noinput
```

---

## Récapitulatif architecture finale

```
┌─────────────────────────────────────────────────────┐
│                    RAILWAY                           │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────┐  ┌────────┐ │
│  │   WEB    │  │  WORKER  │  │  DB  │  │ REDIS  │ │
│  │ Django   │  │  Celery  │  │ PG   │  │ Cache  │ │
│  │Gunicorn  │  │  Tasks   │  │      │  │ Queue  │ │
│  └────┬─────┘  └────┬─────┘  └──────┘  └────────┘ │
└───────┼─────────────┼───────────────────────────────┘
        │             │
        ▼             ▼
   REST API      Tâches async
   (Flutter)     ┌────────────┐
                 │  Resend    │ ← Emails
                 │  FCM       │ ← Push Flutter
                 │  Claude    │ ← AI Vision
                 │  Cloudinary│ ← Photos
                 └────────────┘
```

---

*Prompt généré pour le projet EcoCycle Haiti — Eliézer Léonce — 2026*
