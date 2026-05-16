# EcoCycle — Prompt d'Intégration Site Web (Django Templates)

> **Objectif** : Intégrer le site web statique EcoCycle dans le projet Django existant sous forme de templates dynamiques. Django servira à la fois l'API REST (Flutter) ET le site web (navigateur).  
> **Prérequis** : Le backend Django EcoCycle est déjà en place avec toutes ses apps (accounts, waste, marketplace, collections, notifications, impact, academy, blog, core).  
> **Fichier de référence** : `ecocycle.html` — le site statique original à rendre dynamique.

---

## TABLE DES MATIÈRES

1. [Contexte & Architecture](#1-contexte--architecture)
2. [Phase W1 — Setup & Base Template](#2-phase-w1--setup--base-template)
3. [Phase W2 — Landing Page Dynamique](#3-phase-w2--landing-page-dynamique)
4. [Phase W3 — Pages d'Authentification](#4-phase-w3--pages-dauthentification)
5. [Phase W4 — Dashboard Utilisateur](#5-phase-w4--dashboard-utilisateur)
6. [Phase W5 — Marketplace Public](#6-phase-w5--marketplace-public)
7. [Phase W6 — Ramassages & Collecte](#7-phase-w6--ramassages--collecte)
8. [Phase W7 — Panel Admin Custom](#8-phase-w7--panel-admin-custom)
9. [Phase W8 — Academy & Blog](#9-phase-w8--academy--blog)
10. [Phase W9 — Finalisation & Polish](#10-phase-w9--finalisation--polish)
11. [Charte graphique](#11-charte-graphique)
12. [Mixins & Utilitaires réutilisables](#12-mixins--utilitaires-réutilisables)

---

## 1. Contexte & Architecture

### Ce qu'on construit

```
ecocycle/ (projet Django existant)
├── apps/              ← API REST existante (NE PAS MODIFIER)
│   ├── accounts/
│   ├── waste/
│   ├── marketplace/
│   ├── collections/
│   ├── notifications/
│   ├── impact/
│   ├── academy/
│   ├── blog/
│   └── core/
│
├── web/               ← NOUVELLE APP (vues web Django)
│   ├── views/
│   │   ├── __init__.py
│   │   ├── auth_views.py
│   │   ├── dashboard_views.py
│   │   ├── marketplace_views.py
│   │   ├── collection_views.py
│   │   ├── admin_views.py
│   │   ├── academy_views.py
│   │   └── blog_views.py
│   ├── mixins.py
│   ├── urls.py
│   └── context_processors.py
│
├── templates/         ← TOUS les templates HTML
│   ├── base.html
│   ├── home.html
│   ├── auth/
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── verify_email.html
│   │   ├── reset_password.html
│   │   └── reset_password_confirm.html
│   ├── dashboard/
│   │   ├── base_dashboard.html
│   │   ├── overview.html
│   │   ├── my_listings.html
│   │   ├── submit_waste.html
│   │   ├── my_orders.html
│   │   ├── my_impact.html
│   │   ├── pickups.html
│   │   ├── request_pickup.html
│   │   ├── pickup_detail.html
│   │   └── profile.html
│   ├── marketplace/
│   │   ├── list.html
│   │   └── detail.html
│   ├── admin_panel/
│   │   ├── base_admin.html
│   │   ├── dashboard.html
│   │   ├── listings.html
│   │   ├── listing_detail.html
│   │   ├── pickups.html
│   │   ├── users.html
│   │   └── orders.html
│   ├── academy/
│   │   ├── list.html
│   │   ├── detail.html
│   │   └── lesson.html
│   ├── blog/
│   │   ├── list.html
│   │   └── detail.html
│   └── errors/
│       ├── 404.html
│       └── 500.html
│
└── static/
    ├── css/
    │   ├── main.css       ← extrait du HTML original
    │   ├── dashboard.css
    │   └── admin.css
    ├── js/
    │   ├── main.js        ← extrait du HTML original
    │   ├── dashboard.js
    │   └── ai_analysis.js
    └── img/
        └── logo.svg
```

### Règle importante

> Les apps existantes (`accounts`, `waste`, `marketplace`, etc.) **ne doivent pas être modifiées**. La nouvelle app `web` importe directement les modèles et les utilise dans ses vues. L'API REST reste intacte pour Flutter.

### Gestion de la session web

Les utilisateurs web se connectent via un formulaire Django classique. On stocke les données user en session :

```python
# À la connexion
request.session['user_id'] = str(user.id)
request.session['user_role'] = user.role
request.session['user_name'] = user.full_name

# Pour accéder à l'utilisateur dans les vues
user = User.objects.get(id=request.session['user_id'])
```

---

## 2. Phase W1 — Setup & Base Template

### Instructions pour Claude Code

```
Tu vas intégrer le site web EcoCycle dans le projet Django existant.
Commence par la Phase W1 uniquement. Ne touche pas aux apps existantes.

ÉTAPE 1 — Mettre à jour config/settings/base.py

Ajoute/modifie ces paramètres :

TEMPLATES[0]['DIRS'] = [BASE_DIR / 'templates']

STATICFILES_DIRS = [BASE_DIR / 'static']

INSTALLED_APPS += ['web']

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

ÉTAPE 2 — Créer l'app web

python manage.py startapp web

Crée la structure de dossiers :
- web/views/ (dossier avec __init__.py)
- templates/ et tous ses sous-dossiers
- static/css/, static/js/, static/img/

ÉTAPE 3 — Extraire les assets du fichier ecocycle.html

Lis ecocycle.html et :
- Extrait tout le CSS dans static/css/main.css
- Extrait tout le JavaScript dans static/js/main.js
- Conserve les polices Google Fonts (Syne + DM Sans) en lien CDN

ÉTAPE 4 — Créer templates/base.html

Ce template est le layout de toutes les pages. Il doit contenir :

<!DOCTYPE html>
<html lang="fr">
<head>
  {% load static %}
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}EcoCycle Haiti{% endblock %} — Recyclez, Gagnez, Impactez</title>
  <meta name="description" content="{% block meta_description %}Plateforme de recyclage intelligent en Haïti{% endblock %}">
  <!-- Google Fonts -->
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{% static 'css/main.css' %}">
  {% block extra_css %}{% endblock %}
</head>
<body>

  <!-- NAVBAR DYNAMIQUE -->
  <nav class="navbar">
    <div class="nav-container">
      <a href="{% url 'home' %}" class="nav-logo">
        <span class="logo-icon">♻</span> EcoCycle
      </a>
      <ul class="nav-menu">
        <li><a href="{% url 'home' %}">Accueil</a></li>
        <li><a href="{% url 'marketplace' %}">Marketplace</a></li>
        <li><a href="{% url 'blog_list' %}">Blog</a></li>
        <li><a href="{% url 'academy_list' %}">Academy</a></li>
        <li><a href="{% url 'home' %}#contact">Contact</a></li>
      </ul>
      <div class="nav-actions">
        {% if request.session.user_id %}
          <div class="user-menu">
            <span class="user-name">{{ request.session.user_name }}</span>
            <a href="{% url 'dashboard' %}" class="btn btn-outline">Dashboard</a>
            {% if request.session.user_role == 'admin' %}
              <a href="{% url 'admin_panel' %}" class="btn btn-warning">Admin</a>
            {% endif %}
            <a href="{% url 'web_logout' %}" class="btn btn-ghost">Déconnexion</a>
          </div>
        {% else %}
          <a href="{% url 'web_login' %}" class="btn btn-outline">Connexion</a>
          <a href="{% url 'web_register' %}" class="btn btn-primary">S'inscrire</a>
        {% endif %}
      </div>
      <button class="hamburger" id="hamburger">☰</button>
    </div>
  </nav>

  <!-- MESSAGES FLASH -->
  {% if messages %}
    <div class="messages-container">
      {% for message in messages %}
        <div class="alert alert-{{ message.tags }}">
          {{ message }}
          <button class="alert-close" onclick="this.parentElement.remove()">×</button>
        </div>
      {% endfor %}
    </div>
  {% endif %}

  <!-- CONTENU PRINCIPAL -->
  <main>
    {% block content %}{% endblock %}
  </main>

  <!-- FOOTER (copié du HTML original) -->
  <footer class="footer">
    <!-- Coller ici le footer complet du HTML original -->
    <div class="footer-content">
      <div class="footer-brand">
        <span class="logo-icon">♻</span> EcoCycle Haiti
        <p>Transformez vos déchets en opportunités économiques.</p>
      </div>
      <div class="footer-links">
        <a href="{% url 'home' %}">Accueil</a>
        <a href="{% url 'marketplace' %}">Marketplace</a>
        <a href="{% url 'blog_list' %}">Blog</a>
        <a href="{% url 'academy_list' %}">Academy</a>
      </div>
    </div>
    <div class="footer-bottom">
      <p>© 2026 EcoCycle Haiti — Tous droits réservés</p>
    </div>
  </footer>

  <script src="{% static 'js/main.js' %}"></script>
  {% block extra_js %}{% endblock %}
</body>
</html>

ÉTAPE 5 — Créer web/mixins.py

from django.shortcuts import redirect
from django.contrib import messages
from apps.accounts.models import User


class LoginRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('user_id'):
            messages.error(request, 'Connectez-vous pour accéder à cette page.')
            return redirect('web_login')
        return super().dispatch(request, *args, **kwargs)

    def get_current_user(self, request):
        try:
            return User.objects.get(id=request.session['user_id'])
        except User.DoesNotExist:
            return None


class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        if request.session.get('user_role') != 'admin':
            messages.error(request, 'Accès réservé aux administrateurs.')
            return redirect('dashboard')
        return result


class CollectorRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        if request.session.get('user_role') not in ['collector', 'admin']:
            messages.error(request, 'Accès réservé aux collecteurs.')
            return redirect('dashboard')
        return result


ÉTAPE 6 — Créer web/views/__init__.py avec une HomeView basique

from django.views.generic import TemplateView

class HomeView(TemplateView):
    template_name = 'home.html'

ÉTAPE 7 — Créer web/urls.py

from django.urls import path
from .views import HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
]

ÉTAPE 8 — Connecter dans config/urls.py

Ajoute en PREMIER dans urlpatterns (avant les routes api/) :
path('', include('web.urls')),

ÉTAPE 9 — Créer templates/home.html minimal

{% extends 'base.html' %}
{% block content %}
<h1>EcoCycle Haiti — Site en construction</h1>
{% endblock %}

Lance python manage.py runserver et vérifie :
- http://127.0.0.1:8000/ affiche la navbar + footer + le titre
- Aucune erreur dans la console
Dis-moi quand c'est terminé.
```

---

## 3. Phase W2 — Landing Page Dynamique

### Instructions pour Claude Code

```
Phase W1 validée. Passe à la Phase W2 : landing page dynamique.

ÉTAPE 1 — Mettre à jour web/views/__init__.py (HomeView)

from django.views.generic import TemplateView
from django.db.models import Sum, Count
from apps.impact.models import ImpactRecord
from apps.accounts.models import User
from apps.marketplace.models import Auction, Order
from apps.collections.models import PickupRequest
from apps.waste.models import WasteListing
from django.core.cache import cache


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Stats globales — cachées 5 minutes
        stats = cache.get('home_stats')
        if not stats:
            agg = ImpactRecord.objects.aggregate(
                total_kg=Sum('kg_recycled'),
                total_co2=Sum('co2_saved_kg'),
            )
            stats = {
                'total_kg_recycled': int(agg['total_kg'] or 0),
                'total_co2_saved': int(agg['total_co2'] or 0),
                'total_users': User.objects.filter(is_active=True).count(),
                'total_collections': PickupRequest.objects.filter(status='completed').count(),
            }
            cache.set('home_stats', stats, 300)

        context['stats'] = stats

        # 6 dernières enchères actives pour la section marketplace
        from django.utils import timezone
        context['featured_auctions'] = Auction.objects.filter(
            status='active',
            ends_at__gt=timezone.now()
        ).select_related('listing', 'listing__category').order_by('-created_at')[:6]

        return context


ÉTAPE 2 — Créer templates/home.html

Ce template étend base.html et reproduit TOUTES les sections du fichier
ecocycle.html original, mais avec des données dynamiques.

Structure du template :

{% extends 'base.html' %}
{% load static %}

{% block content %}

<!-- 1. HERO SECTION (copie exacte du HTML original) -->
<!-- Remplacer les stats hardcodées par : -->
<span class="stat-number" data-target="{{ stats.total_kg_recycled }}">0</span>
<span class="stat-number" data-target="{{ stats.total_users }}">0</span>
<span class="stat-number" data-target="{{ stats.total_collections }}">0</span>

<!-- 2. HOW IT WORKS (statique — copie du HTML original) -->

<!-- 3. FEATURES (statique — copie du HTML original) -->

<!-- 4. STATS ANIMÉES -->
<div class="stat-item">
  <span class="counter" data-target="{{ stats.total_kg_recycled }}">0</span>
  <span>kg recyclés</span>
</div>
<div class="stat-item">
  <span class="counter" data-target="{{ stats.total_users }}">0</span>
  <span>utilisateurs actifs</span>
</div>
<div class="stat-item">
  <span class="counter" data-target="{{ stats.total_collections }}">0</span>
  <span>collectes réalisées</span>
</div>
<div class="stat-item">
  <span class="counter" data-target="{{ stats.total_co2_saved }}">0</span>
  <span>kg CO₂ économisés</span>
</div>

<!-- 5. MARKETPLACE PREVIEW -->
<section class="marketplace-preview">
  <h2>Dernières annonces</h2>
  <div class="listings-grid">
    {% for auction in featured_auctions %}
    <div class="listing-card">
      {% if auction.listing.photo %}
        <img src="{{ auction.listing.photo.url }}" alt="{{ auction.listing.title }}">
      {% endif %}
      <div class="card-body">
        <span class="badge badge-category">{{ auction.listing.category.name }}</span>
        <h3>{{ auction.listing.title }}</h3>
        <p class="city">📍 {{ auction.listing.city }}</p>
        <div class="price-row">
          <span class="price">{{ auction.current_price }} HTG</span>
          <span class="bids">{{ auction.total_bids }} enchères</span>
        </div>
        <a href="{% url 'auction_detail' auction.id %}" class="btn btn-primary btn-sm">
          Voir l'enchère
        </a>
      </div>
    </div>
    {% empty %}
    <p>Aucune enchère active pour le moment.</p>
    {% endfor %}
  </div>
  <div class="text-center">
    <a href="{% url 'marketplace' %}" class="btn btn-outline btn-lg">
      Voir toutes les annonces →
    </a>
  </div>
</section>

<!-- 6. BENEFITS (statique — copie du HTML original) -->

<!-- 7. ACADEMY PREVIEW (statique) -->

<!-- 8. TESTIMONIALS (statique — copie du HTML original) -->

<!-- 9. PARTNERS (statique — copie du HTML original) -->

<!-- 10. APP DOWNLOAD (statique — copie du HTML original) -->

<!-- 11. FAQ (statique — garder l'accordéon JS du HTML original) -->

<!-- 12. CONTACT FORM -->
<section id="contact">
  <form method="POST" action="{% url 'contact' %}">
    {% csrf_token %}
    <input type="text" name="first_name" placeholder="Prénom" required>
    <input type="text" name="last_name" placeholder="Nom" required>
    <input type="email" name="email" placeholder="Email" required>
    <input type="text" name="subject" placeholder="Sujet" required>
    <textarea name="message" placeholder="Votre message" required></textarea>
    <button type="submit" class="btn btn-primary">Envoyer le message</button>
  </form>
</section>

<!-- 13. NEWSLETTER -->
<section id="newsletter">
  <form method="POST" action="{% url 'newsletter_subscribe' %}">
    {% csrf_token %}
    <input type="email" name="email" placeholder="Votre adresse email" required>
    <button type="submit" class="btn btn-primary">S'abonner</button>
  </form>
</section>

{% endblock %}

ÉTAPE 3 — Mettre à jour web/urls.py avec les routes contact et newsletter

from django.urls import path
from .views import HomeView
from apps.core.views import ContactView, NewsletterSubscribeView, NewsletterConfirmView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('newsletter/subscribe/', NewsletterSubscribeView.as_view(), name='newsletter_subscribe'),
    path('newsletter/confirm/<uuid:token>/', NewsletterConfirmView.as_view(), name='newsletter_confirm'),
]

ÉTAPE 4 — Modifier apps/core/views.py ContactView et NewsletterSubscribeView

Pour les vues web (non API), si la requête vient du navigateur (pas d'Accept: application/json),
rediriger vers la home avec un message flash au lieu de retourner du JSON :

from django.contrib import messages
from django.shortcuts import redirect

class ContactView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # ... code existant ...
        if request.accepted_media_type == 'text/html':
            messages.success(request, 'Message envoyé avec succès ! Nous vous répondrons bientôt.')
            return redirect('home')
        return Response({'message': 'Message envoyé.'}, status=201)

Lance python manage.py runserver et vérifie que :
- La landing page s'affiche complètement avec toutes les sections du HTML original
- Les stats affichent les vraies données (même si 0 pour l'instant)
- Les cards marketplace s'affichent (vides si pas encore de données)
- Le form contact fonctionne
Dis-moi quand c'est terminé.
```

---

## 4. Phase W3 — Pages d'Authentification

### Instructions pour Claude Code

```
Phase W2 validée. Passe à la Phase W3 : pages d'authentification.

ÉTAPE 1 — Créer web/views/auth_views.py

from django.views.generic import View, TemplateView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.models import User, EmailVerificationToken, PasswordResetToken
from apps.accounts.tasks import send_verification_email, send_password_reset_email
from web.mixins import LoginRequiredMixin
import uuid


class WebLoginView(View):
    template_name = 'auth/login.html'

    def get(self, request):
        if request.session.get('user_id'):
            return redirect('dashboard')
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=email, password=password)
        if not user:
            return render(request, self.template_name, {
                'error': 'Email ou mot de passe incorrect.',
                'email': email,
            })
        if not user.is_active:
            return render(request, self.template_name, {
                'error': 'Ce compte est désactivé.'
            })

        # Stocker en session
        request.session['user_id'] = str(user.id)
        request.session['user_role'] = user.role
        request.session['user_name'] = user.full_name
        request.session['user_email'] = user.email

        messages.success(request, f'Bienvenue, {user.first_name} !')

        next_url = request.GET.get('next', 'dashboard')
        if user.role == 'admin':
            return redirect('admin_panel')
        return redirect(next_url)


class WebRegisterView(View):
    template_name = 'auth/register.html'

    def get(self, request):
        if request.session.get('user_id'):
            return redirect('dashboard')
        return render(request, self.template_name)

    def post(self, request):
        data = request.POST
        errors = {}

        # Validation
        if not data.get('first_name'):
            errors['first_name'] = 'Prénom requis.'
        if not data.get('last_name'):
            errors['last_name'] = 'Nom requis.'
        if not data.get('email'):
            errors['email'] = 'Email requis.'
        elif User.objects.filter(email=data['email']).exists():
            errors['email'] = 'Cet email est déjà utilisé.'
        if not data.get('password') or len(data.get('password', '')) < 8:
            errors['password'] = 'Mot de passe : 8 caractères minimum.'
        if data.get('password') != data.get('password_confirm'):
            errors['password_confirm'] = 'Les mots de passe ne correspondent pas.'

        if errors:
            return render(request, self.template_name, {'errors': errors, 'data': data})

        user = User.objects.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone', ''),
        )
        send_verification_email.delay(str(user.id))

        messages.success(request, 'Compte créé ! Vérifiez votre email pour activer votre compte.')
        return redirect('web_login')


class WebLogoutView(LoginRequiredMixin, View):
    def get(self, request):
        request.session.flush()
        messages.info(request, 'Vous êtes déconnecté.')
        return redirect('home')


class VerifyEmailWebView(View):
    def get(self, request, token):
        try:
            verification = EmailVerificationToken.objects.get(token=token)
            if not verification.is_valid():
                messages.error(request, 'Ce lien de vérification a expiré.')
                return redirect('web_login')
            verification.user.is_email_verified = True
            verification.user.save()
            verification.delete()
            messages.success(request, 'Email vérifié ! Vous pouvez vous connecter.')
        except EmailVerificationToken.DoesNotExist:
            messages.error(request, 'Lien invalide.')
        return redirect('web_login')


class ResetPasswordWebView(View):
    template_name = 'auth/reset_password.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email', '').strip()
        try:
            user = User.objects.get(email=email)
            send_password_reset_email.delay(str(user.id))
        except User.DoesNotExist:
            pass
        messages.info(request, 'Si cet email existe, un lien de réinitialisation a été envoyé.')
        return redirect('web_login')


class ResetPasswordConfirmWebView(View):
    template_name = 'auth/reset_password_confirm.html'

    def get(self, request, token):
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            if not reset_token.is_valid():
                messages.error(request, 'Ce lien a expiré.')
                return redirect('reset_password')
        except PasswordResetToken.DoesNotExist:
            messages.error(request, 'Lien invalide.')
            return redirect('reset_password')
        return render(request, self.template_name, {'token': token})

    def post(self, request, token):
        password = request.POST.get('new_password', '')
        confirm = request.POST.get('password_confirm', '')
        if password != confirm or len(password) < 8:
            return render(request, self.template_name, {
                'token': token,
                'error': 'Mots de passe invalides (8 caractères minimum).'
            })
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            reset_token.user.set_password(password)
            reset_token.user.save()
            reset_token.used = True
            reset_token.save()
            messages.success(request, 'Mot de passe réinitialisé. Connectez-vous.')
        except PasswordResetToken.DoesNotExist:
            messages.error(request, 'Token invalide.')
        return redirect('web_login')


ÉTAPE 2 — Créer les templates auth/

templates/auth/login.html :
{% extends 'base.html' %}
{% block title %}Connexion{% endblock %}
{% block content %}
<div class="auth-container">
  <div class="auth-card">
    <div class="auth-logo">♻ EcoCycle</div>
    <h2>Bienvenue</h2>
    <p class="auth-subtitle">Connectez-vous à votre compte</p>

    {% if error %}
      <div class="alert alert-error">{{ error }}</div>
    {% endif %}

    <form method="POST" action="{% url 'web_login' %}">
      {% csrf_token %}
      <div class="form-group">
        <label>Email</label>
        <input type="email" name="email" value="{{ email|default:'' }}"
               placeholder="votre@email.com" required class="form-control">
      </div>
      <div class="form-group">
        <label>Mot de passe</label>
        <input type="password" name="password" placeholder="••••••••"
               required class="form-control">
        <a href="{% url 'reset_password' %}" class="forgot-link">Mot de passe oublié ?</a>
      </div>
      <button type="submit" class="btn btn-primary btn-full">Se connecter</button>
    </form>

    <p class="auth-switch">
      Pas encore de compte ?
      <a href="{% url 'web_register' %}">S'inscrire gratuitement</a>
    </p>
  </div>
</div>
{% endblock %}

templates/auth/register.html :
{% extends 'base.html' %}
{% block title %}Inscription{% endblock %}
{% block content %}
<div class="auth-container">
  <div class="auth-card auth-card-wide">
    <div class="auth-logo">♻ EcoCycle</div>
    <h2>Créer un compte</h2>
    <p class="auth-subtitle">Rejoignez la communauté EcoCycle Haiti</p>

    <form method="POST" action="{% url 'web_register' %}">
      {% csrf_token %}
      <div class="form-row">
        <div class="form-group">
          <label>Prénom *</label>
          <input type="text" name="first_name" value="{{ data.first_name|default:'' }}"
                 class="form-control {% if errors.first_name %}is-invalid{% endif %}" required>
          {% if errors.first_name %}<span class="error-msg">{{ errors.first_name }}</span>{% endif %}
        </div>
        <div class="form-group">
          <label>Nom *</label>
          <input type="text" name="last_name" value="{{ data.last_name|default:'' }}"
                 class="form-control {% if errors.last_name %}is-invalid{% endif %}" required>
          {% if errors.last_name %}<span class="error-msg">{{ errors.last_name }}</span>{% endif %}
        </div>
      </div>
      <div class="form-group">
        <label>Email *</label>
        <input type="email" name="email" value="{{ data.email|default:'' }}"
               class="form-control {% if errors.email %}is-invalid{% endif %}" required>
        {% if errors.email %}<span class="error-msg">{{ errors.email }}</span>{% endif %}
      </div>
      <div class="form-group">
        <label>Téléphone</label>
        <input type="tel" name="phone" value="{{ data.phone|default:'' }}"
               placeholder="+509 xxxx xxxx" class="form-control">
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Mot de passe *</label>
          <input type="password" name="password"
                 class="form-control {% if errors.password %}is-invalid{% endif %}" required>
          {% if errors.password %}<span class="error-msg">{{ errors.password }}</span>{% endif %}
        </div>
        <div class="form-group">
          <label>Confirmer *</label>
          <input type="password" name="password_confirm"
                 class="form-control {% if errors.password_confirm %}is-invalid{% endif %}" required>
          {% if errors.password_confirm %}<span class="error-msg">{{ errors.password_confirm }}</span>{% endif %}
        </div>
      </div>
      <button type="submit" class="btn btn-primary btn-full">Créer mon compte</button>
    </form>

    <p class="auth-switch">
      Déjà un compte ? <a href="{% url 'web_login' %}">Se connecter</a>
    </p>
  </div>
</div>
{% endblock %}

Crée aussi auth/reset_password.html et auth/reset_password_confirm.html
avec le même style de carte centrée.

ÉTAPE 3 — Ajouter le CSS auth dans static/css/main.css

Ajoute les styles pour :
.auth-container { centré, min-height: 80vh, display flex, align-items center }
.auth-card { background white, border-radius 16px, padding 40px, box-shadow, max-width 460px, width 100% }
.auth-card-wide { max-width 600px }
.form-row { display grid, grid-template-columns 1fr 1fr, gap 16px }
.form-group { display flex, flex-direction column, gap 6px }
.form-control { border 2px solid #e5e7eb, border-radius 8px, padding 12px 16px }
.form-control:focus { border-color #0d7a45, outline none }
.form-control.is-invalid { border-color #ef4444 }
.error-msg { color #ef4444, font-size 12px }
.btn-full { width 100% }
.forgot-link { font-size 13px, color #0d7a45, text-align right }
.auth-switch { text-align center, margin-top 20px, color #666 }

ÉTAPE 4 — Mettre à jour web/urls.py

from .views.auth_views import (
    WebLoginView, WebRegisterView, WebLogoutView,
    VerifyEmailWebView, ResetPasswordWebView, ResetPasswordConfirmWebView
)

urlpatterns += [
    path('login/', WebLoginView.as_view(), name='web_login'),
    path('register/', WebRegisterView.as_view(), name='web_register'),
    path('logout/', WebLogoutView.as_view(), name='web_logout'),
    path('verify-email/<uuid:token>/', VerifyEmailWebView.as_view(), name='verify_email_web'),
    path('reset-password/', ResetPasswordWebView.as_view(), name='reset_password'),
    path('reset-password/confirm/<uuid:token>/', ResetPasswordConfirmWebView.as_view(), name='reset_password_confirm_web'),
]

ÉTAPE 5 — Mettre à jour config/settings/base.py

Remplace dans TEMPLATES la valeur 'context_processors' pour ajouter :
'django.template.context_processors.request',

Teste :
- Inscription d'un nouveau user
- Connexion avec cet user
- Vérification que la nav change (nom affiché + bouton dashboard)
- Déconnexion
- Mot de passe oublié
Dis-moi quand c'est terminé.
```

---

## 5. Phase W4 — Dashboard Utilisateur

### Instructions pour Claude Code

```
Phase W3 validée. Passe à la Phase W4 : dashboard utilisateur.

ÉTAPE 1 — Créer web/views/dashboard_views.py

Toutes les vues héritent de LoginRequiredMixin.
Les données viennent directement des modèles Django (pas d'appels HTTP internes).

from django.views.generic import View, TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from web.mixins import LoginRequiredMixin
from apps.accounts.models import User
from apps.waste.models import WasteListing, WasteCategory
from apps.marketplace.models import Auction, Order
from apps.collections.models import PickupRequest
from apps.impact.models import UserImpactSummary, ImpactRecord
from apps.notifications.models import Notification


class DashboardOverviewView(LoginRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        summary, _ = UserImpactSummary.objects.get_or_create(user=user)
        notifications = Notification.objects.filter(user=user, is_read=False)[:5]
        recent_listings = WasteListing.objects.filter(user=user).order_by('-created_at')[:5]

        return render(request, 'dashboard/overview.html', {
            'user': user,
            'summary': summary,
            'notifications': notifications,
            'recent_listings': recent_listings,
            'listings_count': WasteListing.objects.filter(user=user).count(),
            'pending_count': WasteListing.objects.filter(user=user, status='pending_review').count(),
        })


class MyListingsView(LoginRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        status_filter = request.GET.get('status', '')
        listings = WasteListing.objects.filter(user=user).select_related('category')
        if status_filter:
            listings = listings.filter(status=status_filter)
        return render(request, 'dashboard/my_listings.html', {
            'user': user,
            'listings': listings,
            'status_filter': status_filter,
        })


class SubmitWasteView(LoginRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        categories = WasteCategory.objects.filter(is_active=True)
        return render(request, 'dashboard/submit_waste.html', {
            'user': user,
            'categories': categories,
        })

    def post(self, request):
        user = self.get_current_user(request)
        listing = WasteListing.objects.create(
            user=user,
            title=request.POST.get('title', ''),
            description=request.POST.get('description', ''),
            category_id=request.POST.get('category') or None,
            quantity_kg=request.POST.get('quantity_kg', 1),
            photo=request.FILES.get('photo'),
            pickup_address=request.POST.get('pickup_address', ''),
            city=request.POST.get('city', ''),
            status='pending_review',
        )
        from apps.waste.tasks import analyze_waste_photo_async, notify_admin_new_listing
        analyze_waste_photo_async.delay(str(listing.id))
        notify_admin_new_listing.delay(str(listing.id))
        messages.success(request, 'Votre déchet a été soumis ! L\'analyse IA est en cours.')
        return redirect('my_listings')


class MyOrdersView(LoginRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        orders = Order.objects.filter(buyer=user).select_related(
            'auction', 'auction__listing', 'seller'
        ).order_by('-created_at')
        return render(request, 'dashboard/my_orders.html', {
            'user': user,
            'orders': orders,
        })


class MyImpactView(LoginRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        summary, _ = UserImpactSummary.objects.get_or_create(user=user)
        records = ImpactRecord.objects.filter(user=user).order_by('-created_at')[:20]
        return render(request, 'dashboard/my_impact.html', {
            'user': user,
            'summary': summary,
            'records': records,
        })


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        return render(request, 'dashboard/profile.html', {'user': user})

    def post(self, request):
        user = self.get_current_user(request)
        action = request.POST.get('action')

        if action == 'update_profile':
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.phone = request.POST.get('phone', user.phone)
            user.bio = request.POST.get('bio', user.bio)
            user.address = request.POST.get('address', user.address)
            user.city = request.POST.get('city', user.city)
            if request.FILES.get('avatar'):
                user.avatar = request.FILES['avatar']
            user.save()
            request.session['user_name'] = user.full_name
            messages.success(request, 'Profil mis à jour.')

        elif action == 'change_password':
            old_pwd = request.POST.get('old_password')
            new_pwd = request.POST.get('new_password')
            confirm = request.POST.get('password_confirm')
            if not user.check_password(old_pwd):
                messages.error(request, 'Mot de passe actuel incorrect.')
            elif new_pwd != confirm or len(new_pwd) < 8:
                messages.error(request, 'Nouveau mot de passe invalide.')
            else:
                user.set_password(new_pwd)
                user.save()
                messages.success(request, 'Mot de passe modifié.')

        return redirect('profile')


ÉTAPE 2 — Créer templates/dashboard/base_dashboard.html

{% extends 'base.html' %}
{% load static %}

{% block content %}
<div class="dashboard-layout">

  <!-- SIDEBAR -->
  <aside class="sidebar">
    <div class="sidebar-user">
      {% if user.avatar %}
        <img src="{{ user.avatar.url }}" alt="Avatar" class="sidebar-avatar">
      {% else %}
        <div class="sidebar-avatar-placeholder">
          {{ user.first_name|slice:":1" }}{{ user.last_name|slice:":1" }}
        </div>
      {% endif %}
      <div>
        <p class="sidebar-name">{{ user.full_name }}</p>
        <span class="role-badge role-{{ user.role }}">{{ user.get_role_display }}</span>
      </div>
    </div>

    <nav class="sidebar-nav">
      <a href="{% url 'dashboard' %}" class="sidebar-link {% if request.resolver_match.url_name == 'dashboard' %}active{% endif %}">
        🏠 Vue d'ensemble
      </a>
      <a href="{% url 'my_listings' %}" class="sidebar-link {% if 'listing' in request.resolver_match.url_name %}active{% endif %}">
        ♻️ Mes déchets
      </a>
      <a href="{% url 'marketplace' %}" class="sidebar-link">
        🏪 Marketplace
      </a>
      <a href="{% url 'my_orders' %}" class="sidebar-link {% if request.resolver_match.url_name == 'my_orders' %}active{% endif %}">
        🛒 Mes commandes
      </a>
      <a href="{% url 'my_pickups' %}" class="sidebar-link {% if 'pickup' in request.resolver_match.url_name %}active{% endif %}">
        🚚 Ramassages
      </a>
      <a href="{% url 'my_impact' %}" class="sidebar-link {% if request.resolver_match.url_name == 'my_impact' %}active{% endif %}">
        🌱 Mon impact
      </a>
      <a href="{% url 'profile' %}" class="sidebar-link {% if request.resolver_match.url_name == 'profile' %}active{% endif %}">
        👤 Mon profil
      </a>
    </nav>
  </aside>

  <!-- CONTENU -->
  <div class="dashboard-content">
    {% block dashboard_content %}{% endblock %}
  </div>

</div>
{% endblock %}

ÉTAPE 3 — Créer les templates dashboard/

dashboard/overview.html :
- Cards stats : listings soumis, kg recyclés, CO2 économisé, rang
- Section notifications récentes (5 non lues)
- Section derniers listings avec statuts colorés

dashboard/my_listings.html :
- Bouton vert "Soumettre un déchet" en haut
- Filtres par statut (tous / en attente / approuvé / vendu)
- Table ou grid avec : photo miniature, titre, catégorie, statut badge, valeur AI, date
- Statuts : draft=gris, pending_review=orange, approved=vert, sold=bleu, rejected=rouge

dashboard/submit_waste.html :
- Form upload photo avec preview JavaScript
- Select catégorie
- Champs : titre, description, poids estimé (kg), adresse de ramassage, ville
- Bouton "Analyser avec l'IA" (AJAX — appelle /api/waste/analyze/)
- Zone résultat AI qui apparaît : catégorie détectée, valeur HTG, score recyclabilité (0-10), état
- Bouton "Publier ce listing" (submit du form)

Le JavaScript pour l'analyse AI (dans static/js/ai_analysis.js) :
document.getElementById('btn-analyze').addEventListener('click', async () => {
  const fileInput = document.getElementById('photo-input');
  const file = fileInput.files[0];
  if (!file) { alert('Sélectionnez une photo d\'abord.'); return; }

  const reader = new FileReader();
  reader.onload = async (e) => {
    const base64 = e.target.result;
    document.getElementById('ai-loading').style.display = 'block';

    const response = await fetch('/api/waste/analyze/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
      },
      body: JSON.stringify({ image_base64: base64 }),
    });

    const data = await response.json();
    document.getElementById('ai-loading').style.display = 'none';

    if (data.analysis) {
      const a = data.analysis;
      document.getElementById('ai-result').style.display = 'block';
      document.getElementById('ai-category').textContent = a.category;
      document.getElementById('ai-value').textContent = a.estimated_value_htg + ' HTG';
      document.getElementById('ai-score').textContent = a.recyclability_score + '/10';
      document.getElementById('ai-condition').textContent = a.condition;
      document.getElementById('ai-description').textContent = a.description;
      // Pré-remplir les champs du form
      if (!document.getElementById('title-input').value)
        document.getElementById('title-input').value = a.category;
      if (!document.getElementById('weight-input').value)
        document.getElementById('weight-input').value = a.estimated_weight_kg;
    }
  };
  reader.readAsDataURL(file);
});

dashboard/my_orders.html : table des commandes
dashboard/my_impact.html : stats CO2, graphique barres CSS, historique
dashboard/profile.html : deux sections — infos profil + changement mdp

ÉTAPE 4 — Ajouter le CSS dashboard dans static/css/dashboard.css

.dashboard-layout { display grid; grid-template-columns 260px 1fr; min-height 100vh }
.sidebar { background #1a1a2e; padding 24px; position sticky; top 0; height 100vh; overflow-y auto }
.sidebar-link { display block; padding 12px 16px; color #ccc; border-radius 8px; text-decoration none }
.sidebar-link:hover, .sidebar-link.active { background #0d7a45; color white }
.dashboard-content { padding 32px; background #f5f0e8 }
.stats-grid { display grid; grid-template-columns repeat(4, 1fr); gap 16px; margin-bottom 24px }
.stat-card { background white; border-radius 12px; padding 20px; box-shadow 0 2px 8px rgba(0,0,0,0.06) }
.role-badge { font-size 11px; padding 3px 8px; border-radius 12px; background #e8f5ee; color #0d7a45 }

ÉTAPE 5 — Mettre à jour web/urls.py

from .views.dashboard_views import (
    DashboardOverviewView, MyListingsView, SubmitWasteView,
    MyOrdersView, MyImpactView, ProfileView
)

urlpatterns += [
    path('dashboard/', DashboardOverviewView.as_view(), name='dashboard'),
    path('dashboard/listings/', MyListingsView.as_view(), name='my_listings'),
    path('dashboard/listings/submit/', SubmitWasteView.as_view(), name='submit_waste'),
    path('dashboard/orders/', MyOrdersView.as_view(), name='my_orders'),
    path('dashboard/impact/', MyImpactView.as_view(), name='my_impact'),
    path('dashboard/profile/', ProfileView.as_view(), name='profile'),
]

Teste :
- Login puis accès /dashboard/
- Soumettre un déchet avec une photo → voir l'analyse AI
- Naviguer entre les sections de la sidebar
Dis-moi quand c'est terminé.
```

---

## 6. Phase W6 — Ramassages & Collecte

### Instructions pour Claude Code

```
Phase W5 validée. Passe à la Phase W6 : pages ramassage.

ÉTAPE 1 — Créer web/views/collection_views.py

from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from web.mixins import LoginRequiredMixin, CollectorRequiredMixin
from apps.collections.models import PickupRequest
from apps.accounts.models import User


class MyPickupsView(LoginRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        pickups = PickupRequest.objects.filter(user=user).order_by('-created_at')
        return render(request, 'dashboard/pickups.html', {
            'user': user, 'pickups': pickups
        })


class RequestPickupView(LoginRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        from apps.waste.models import WasteListing
        user_listings = WasteListing.objects.filter(user=user, status='approved')
        return render(request, 'dashboard/request_pickup.html', {
            'user': user, 'user_listings': user_listings
        })

    def post(self, request):
        user = self.get_current_user(request)
        pickup = PickupRequest.objects.create(
            user=user,
            address=request.POST.get('address', ''),
            city=request.POST.get('city', ''),
            preferred_date=request.POST.get('preferred_date'),
            preferred_slot=request.POST.get('preferred_slot', 'morning'),
            special_instructions=request.POST.get('special_instructions', ''),
            listing_id=request.POST.get('listing_id') or None,
        )
        from apps.notifications.tasks import notify_admin_new_pickup
        notify_admin_new_pickup.delay(str(pickup.id))
        messages.success(request, 'Demande de ramassage soumise ! Un collecteur sera assigné bientôt.')
        return redirect('my_pickups')


class PickupDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        user = self.get_current_user(request)
        pickup = get_object_or_404(PickupRequest, pk=pk, user=user)
        return render(request, 'dashboard/pickup_detail.html', {
            'user': user, 'pickup': pickup
        })


ÉTAPE 2 — Créer les templates

dashboard/pickups.html :
- Table des demandes avec badge statut coloré
- Bouton "Nouvelle demande de ramassage" en haut
- Chaque ligne : date, créneau, adresse, statut, bouton "Détail"
- Statuts : requested=orange, assigned=bleu, in_transit=violet, completed=vert, failed=rouge

dashboard/request_pickup.html :
- Form : adresse complète, ville, date souhaitée (date picker), créneau (radio: matin/après-midi/soir)
- Select optionnel "Lier à un listing" (liste des listings approuvés de l'user)
- Textarea instructions spéciales
- Bouton "Soumettre la demande"

dashboard/pickup_detail.html :
- Infos de la demande (adresse, date, créneau)
- Timeline CSS des statuts :
  ● Demandé → ● Assigné → ● En transit → ● Arrivé → ● Complété
  Chaque étape colorée selon l'état actuel
- Si collecteur assigné : afficher nom + téléphone dans une carte
- Historique JSON (status_history) affiché chronologiquement

ÉTAPE 3 — Mettre à jour web/urls.py

from .views.collection_views import MyPickupsView, RequestPickupView, PickupDetailView

urlpatterns += [
    path('dashboard/pickups/', MyPickupsView.as_view(), name='my_pickups'),
    path('dashboard/pickups/request/', RequestPickupView.as_view(), name='request_pickup'),
    path('dashboard/pickups/<uuid:pk>/', PickupDetailView.as_view(), name='pickup_detail'),
]

Dis-moi quand c'est terminé.
```

---

## 7. Phase W5 — Marketplace Public

### Instructions pour Claude Code

```
Phase W4 validée. Passe à la Phase W5 : marketplace public.

ÉTAPE 1 — Créer web/views/marketplace_views.py

from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from web.mixins import LoginRequiredMixin
from apps.marketplace.models import Auction, Bid, Order
from apps.waste.models import WasteCategory


class MarketplaceListView(View):
    def get(self, request):
        auctions = Auction.objects.filter(
            status='active', ends_at__gt=timezone.now()
        ).select_related('listing', 'listing__category', 'seller')

        # Filtres
        category_slug = request.GET.get('category', '')
        city = request.GET.get('city', '')
        sort = request.GET.get('sort', '-created_at')

        if category_slug:
            auctions = auctions.filter(listing__category__slug=category_slug)
        if city:
            auctions = auctions.filter(listing__city__icontains=city)

        sort_map = {
            'price_asc': 'current_price',
            'price_desc': '-current_price',
            'ending_soon': 'ends_at',
            '-created_at': '-created_at',
        }
        auctions = auctions.order_by(sort_map.get(sort, '-created_at'))

        paginator = Paginator(auctions, 12)
        page = paginator.get_page(request.GET.get('page', 1))

        return render(request, 'marketplace/list.html', {
            'auctions': page,
            'categories': WasteCategory.objects.filter(is_active=True),
            'active_category': category_slug,
            'active_sort': sort,
            'city_filter': city,
        })


class AuctionDetailView(View):
    def get(self, request, pk):
        auction = get_object_or_404(
            Auction.objects.select_related('listing', 'listing__category', 'seller'),
            pk=pk
        )
        Auction.objects.filter(pk=pk).update(views_count=auction.views_count + 1)
        bids = auction.bids.order_by('-amount')[:10]
        user_bid = None
        if request.session.get('user_id'):
            user_bid = auction.bids.filter(
                bidder_id=request.session['user_id']
            ).order_by('-amount').first()

        return render(request, 'marketplace/detail.html', {
            'auction': auction,
            'bids': bids,
            'user_bid': user_bid,
            'is_owner': str(auction.seller.id) == request.session.get('user_id', ''),
        })


class PlaceBidWebView(LoginRequiredMixin, View):
    """Vue AJAX pour placer une enchère."""
    def post(self, request, pk):
        auction = get_object_or_404(Auction, pk=pk)
        user = self.get_current_user(request)

        if not auction.is_active:
            return JsonResponse({'error': 'Enchère clôturée.'}, status=400)
        if auction.seller == user:
            return JsonResponse({'error': 'Vous ne pouvez pas enchérir sur votre listing.'}, status=400)

        try:
            amount = float(request.POST.get('amount', 0))
        except ValueError:
            return JsonResponse({'error': 'Montant invalide.'}, status=400)

        min_bid = float(auction.current_price or auction.starting_price) + 10
        if amount < min_bid:
            return JsonResponse({'error': f'Enchère minimum : {min_bid} HTG.'}, status=400)

        auction.bids.filter(is_winning=True).update(is_winning=False)
        bid = Bid.objects.create(auction=auction, bidder=user, amount=amount, is_winning=True)
        auction.current_price = amount
        auction.total_bids += 1
        auction.save()

        from apps.notifications.tasks import notify_new_bid
        notify_new_bid.delay(str(bid.id))

        return JsonResponse({
            'success': True,
            'new_price': str(amount),
            'total_bids': auction.total_bids,
        })


class BuyNowWebView(LoginRequiredMixin, View):
    def post(self, request, pk):
        auction = get_object_or_404(Auction, pk=pk)
        user = self.get_current_user(request)

        if not auction.is_active or not auction.buy_now_price:
            messages.error(request, 'Achat immédiat non disponible.')
            return redirect('auction_detail', pk=pk)
        if auction.seller == user:
            messages.error(request, 'Vous ne pouvez pas acheter votre propre listing.')
            return redirect('auction_detail', pk=pk)

        auction.status = 'sold'
        auction.winner = user
        auction.save()

        order = Order.objects.create(
            auction=auction, buyer=user, seller=auction.seller,
            amount=auction.buy_now_price,
        )
        from apps.notifications.tasks import notify_order_created
        from apps.impact.tasks import create_impact_record
        notify_order_created.delay(str(order.id))
        create_impact_record.delay(str(order.id))

        messages.success(request, f'Achat confirmé ! Commande #{str(order.id)[:8]}')
        return redirect('my_orders')


ÉTAPE 2 — Créer les templates marketplace/

marketplace/list.html :
{% extends 'base.html' %}
{% block title %}Marketplace{% endblock %}
{% block content %}
<div class="marketplace-page">

  <!-- Header -->
  <div class="page-header">
    <h1>🏪 Marketplace EcoCycle</h1>
    <p>Achetez et enchérissez sur des déchets recyclables</p>
  </div>

  <!-- Filtres -->
  <div class="filters-bar">
    <form method="GET" class="filters-form">
      <!-- Filtres catégories (boutons toggle) -->
      <div class="category-filters">
        <a href="?{% if active_sort %}sort={{ active_sort }}{% endif %}"
           class="filter-btn {% if not active_category %}active{% endif %}">Tout</a>
        {% for cat in categories %}
        <a href="?category={{ cat.slug }}{% if active_sort %}&sort={{ active_sort }}{% endif %}"
           class="filter-btn {% if active_category == cat.slug %}active{% endif %}">
          {{ cat.icon }} {{ cat.name }}
        </a>
        {% endfor %}
      </div>
      <!-- Tri et ville -->
      <div class="sort-filters">
        <input type="text" name="city" value="{{ city_filter }}" placeholder="Filtrer par ville">
        <select name="sort" onchange="this.form.submit()">
          <option value="-created_at" {% if active_sort == '-created_at' %}selected{% endif %}>Plus récent</option>
          <option value="price_asc" {% if active_sort == 'price_asc' %}selected{% endif %}>Prix croissant</option>
          <option value="price_desc" {% if active_sort == 'price_desc' %}selected{% endif %}>Prix décroissant</option>
          <option value="ending_soon" {% if active_sort == 'ending_soon' %}selected{% endif %}>Fin proche</option>
        </select>
        <button type="submit" class="btn btn-outline btn-sm">Filtrer</button>
      </div>
    </form>
  </div>

  <!-- Grid auctions -->
  <div class="auctions-grid">
    {% for auction in auctions %}
    <div class="auction-card">
      <div class="auction-img">
        {% if auction.listing.photo %}
          <img src="{{ auction.listing.photo.url }}" alt="{{ auction.listing.title }}">
        {% else %}
          <div class="img-placeholder">{{ auction.listing.category.icon|default:'♻' }}</div>
        {% endif %}
        <span class="category-badge">{{ auction.listing.category.name|default:'Autre' }}</span>
      </div>
      <div class="auction-body">
        <h3>{{ auction.listing.title }}</h3>
        <p class="auction-city">📍 {{ auction.listing.city|default:'Haiti' }}</p>
        <p class="auction-weight">⚖️ {{ auction.listing.quantity_kg }} kg</p>
        <div class="auction-price-row">
          <div>
            <span class="price-label">Prix actuel</span>
            <span class="price">{{ auction.current_price }} HTG</span>
          </div>
          <div>
            <span class="bids-count">{{ auction.total_bids }} enchères</span>
          </div>
        </div>
        <div class="countdown" data-ends="{{ auction.ends_at|date:'c' }}">
          Calcul...
        </div>
        <a href="{% url 'auction_detail' auction.id %}" class="btn btn-primary btn-full">
          Voir l'enchère
        </a>
        {% if auction.buy_now_price %}
          <a href="{% url 'auction_detail' auction.id %}" class="btn btn-outline btn-full btn-sm">
            Acheter — {{ auction.buy_now_price }} HTG
          </a>
        {% endif %}
      </div>
    </div>
    {% empty %}
    <div class="empty-state">
      <p>♻️ Aucune enchère active pour le moment.</p>
      <a href="{% url 'submit_waste' %}" class="btn btn-primary">Soumettre un déchet</a>
    </div>
    {% endfor %}
  </div>

  <!-- Pagination -->
  {% if auctions.has_other_pages %}
  <div class="pagination">
    {% if auctions.has_previous %}
      <a href="?page={{ auctions.previous_page_number }}" class="page-btn">←</a>
    {% endif %}
    <span>Page {{ auctions.number }} / {{ auctions.paginator.num_pages }}</span>
    {% if auctions.has_next %}
      <a href="?page={{ auctions.next_page_number }}" class="page-btn">→</a>
    {% endif %}
  </div>
  {% endif %}

</div>
{% endblock %}

marketplace/detail.html :
- Photo grande + galerie miniatures
- Titre, description, catégorie, poids, ville, état
- Section Analyse AI (si disponible) : score, valeur estimée, recommandations
- Prix actuel + countdown live (JavaScript)
- Historique des 10 dernières enchères
- Form placer enchère (AJAX) — masqué si non connecté ou si vendeur
- Bouton Acheter maintenant (form POST)
- Card vendeur : nom, ville, nb de listings

JavaScript countdown dans static/js/main.js :
document.querySelectorAll('.countdown').forEach(el => {
  const ends = new Date(el.dataset.ends);
  setInterval(() => {
    const diff = ends - new Date();
    if (diff <= 0) { el.textContent = 'Terminée'; return; }
    const d = Math.floor(diff / 86400000);
    const h = Math.floor((diff % 86400000) / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    el.textContent = d > 0 ? `${d}j ${h}h ${m}m` : `${h}h ${m}m ${s}s`;
  }, 1000);
});

ÉTAPE 3 — Mettre à jour web/urls.py

from .views.marketplace_views import (
    MarketplaceListView, AuctionDetailView, PlaceBidWebView, BuyNowWebView
)

urlpatterns += [
    path('marketplace/', MarketplaceListView.as_view(), name='marketplace'),
    path('marketplace/<uuid:pk>/', AuctionDetailView.as_view(), name='auction_detail'),
    path('marketplace/<uuid:pk>/bid/', PlaceBidWebView.as_view(), name='place_bid'),
    path('marketplace/<uuid:pk>/buy-now/', BuyNowWebView.as_view(), name='buy_now'),
]

Dis-moi quand c'est terminé.
```

---

## 8. Phase W7 — Panel Admin Custom

### Instructions pour Claude Code

```
Phase W6 validée. Passe à la Phase W7 : panel admin custom.

IMPORTANT : Ce panel est DIFFÉRENT du /admin/ Django.
Il est accessible sur /panel/ et nécessite role == 'admin'.

ÉTAPE 1 — Créer web/views/admin_views.py

from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from web.mixins import AdminRequiredMixin
from apps.waste.models import WasteListing
from apps.collections.models import PickupRequest
from apps.marketplace.models import Auction, Order
from apps.accounts.models import User
from apps.impact.models import ImpactRecord
from django.db.models import Sum, Count
from django.utils import timezone


class AdminDashboardView(AdminRequiredMixin, View):
    def get(self, request):
        stats = {
            'listings_pending': WasteListing.objects.filter(status='pending_review').count(),
            'listings_total': WasteListing.objects.count(),
            'pickups_unassigned': PickupRequest.objects.filter(status='requested').count(),
            'pickups_total': PickupRequest.objects.count(),
            'auctions_active': Auction.objects.filter(status='active').count(),
            'orders_total': Order.objects.count(),
            'users_total': User.objects.filter(role='user').count(),
            'collectors_total': User.objects.filter(role='collector').count(),
            'total_kg': ImpactRecord.objects.aggregate(t=Sum('kg_recycled'))['t'] or 0,
        }
        recent_listings = WasteListing.objects.filter(
            status='pending_review'
        ).select_related('user', 'category').order_by('-created_at')[:10]

        return render(request, 'admin_panel/dashboard.html', {
            'stats': stats,
            'recent_listings': recent_listings,
        })


class AdminListingsView(AdminRequiredMixin, View):
    def get(self, request):
        status_filter = request.GET.get('status', 'pending_review')
        listings = WasteListing.objects.select_related('user', 'category').order_by('-created_at')
        if status_filter:
            listings = listings.filter(status=status_filter)
        return render(request, 'admin_panel/listings.html', {
            'listings': listings,
            'status_filter': status_filter,
            'pending_count': WasteListing.objects.filter(status='pending_review').count(),
        })


class AdminReviewListingView(AdminRequiredMixin, View):
    def get(self, request, pk):
        listing = get_object_or_404(WasteListing.objects.select_related('user', 'category'), pk=pk)
        return render(request, 'admin_panel/listing_detail.html', {'listing': listing})

    def post(self, request, pk):
        listing = get_object_or_404(WasteListing, pk=pk)
        action = request.POST.get('action')
        user = self.get_current_user(request)
        listing.reviewed_by = user
        listing.reviewed_at = timezone.now()

        if action == 'approve':
            listing.status = 'approved'
            listing.save()
            from apps.notifications.tasks import notify_listing_approved
            notify_listing_approved.delay(str(listing.id))
            messages.success(request, f'Listing "{listing.title}" approuvé.')
        elif action == 'reject':
            listing.status = 'rejected'
            listing.rejection_reason = request.POST.get('rejection_reason', '')
            listing.save()
            from apps.notifications.tasks import notify_listing_rejected
            notify_listing_rejected.delay(str(listing.id))
            messages.warning(request, f'Listing "{listing.title}" rejeté.')

        return redirect('admin_listings')


class AdminPickupsView(AdminRequiredMixin, View):
    def get(self, request):
        status_filter = request.GET.get('status', 'requested')
        pickups = PickupRequest.objects.select_related('user', 'collector').order_by('-created_at')
        if status_filter:
            pickups = pickups.filter(status=status_filter)
        collectors = User.objects.filter(role='collector', is_active=True)
        return render(request, 'admin_panel/pickups.html', {
            'pickups': pickups,
            'collectors': collectors,
            'status_filter': status_filter,
            'unassigned_count': PickupRequest.objects.filter(status='requested').count(),
        })

    def post(self, request):
        pickup_id = request.POST.get('pickup_id')
        collector_id = request.POST.get('collector_id')
        pickup = get_object_or_404(PickupRequest, pk=pickup_id)
        collector = get_object_or_404(User, pk=collector_id, role__in=['collector', 'admin'])
        pickup.collector = collector
        pickup.update_status('assigned', f'Assigné à {collector.full_name}')
        from apps.notifications.tasks import notify_collector_assigned
        notify_collector_assigned.delay(str(pickup.id))
        messages.success(request, f'Ramassage assigné à {collector.full_name}.')
        return redirect('admin_pickups')


class AdminUsersView(AdminRequiredMixin, View):
    def get(self, request):
        role_filter = request.GET.get('role', '')
        users = User.objects.order_by('-created_at')
        if role_filter:
            users = users.filter(role=role_filter)
        return render(request, 'admin_panel/users.html', {
            'users': users, 'role_filter': role_filter
        })

    def post(self, request):
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        target_user = get_object_or_404(User, pk=user_id)

        if action == 'toggle_active':
            target_user.is_active = not target_user.is_active
            target_user.save()
            status = 'activé' if target_user.is_active else 'désactivé'
            messages.success(request, f'Compte {status}.')
        elif action == 'change_role':
            new_role = request.POST.get('new_role')
            if new_role in ['user', 'collector', 'admin']:
                target_user.role = new_role
                target_user.save()
                messages.success(request, f'Rôle changé en {new_role}.')

        return redirect('admin_users')


class AdminOrdersView(AdminRequiredMixin, View):
    def get(self, request):
        orders = Order.objects.select_related(
            'buyer', 'seller', 'auction__listing'
        ).order_by('-created_at')
        return render(request, 'admin_panel/orders.html', {'orders': orders})


ÉTAPE 2 — Créer templates/admin_panel/base_admin.html

{% extends 'base.html' %}
{% block content %}
<div class="admin-layout">
  <aside class="admin-sidebar">
    <h2 class="admin-title">⚙️ Admin Panel</h2>
    <nav>
      <a href="{% url 'admin_panel' %}" class="admin-link">📊 Dashboard</a>
      <a href="{% url 'admin_listings' %}" class="admin-link">
        ♻️ Listings
        {% if pending_count %}<span class="badge-count">{{ pending_count }}</span>{% endif %}
      </a>
      <a href="{% url 'admin_pickups' %}" class="admin-link">🚚 Ramassages</a>
      <a href="{% url 'admin_users' %}" class="admin-link">👥 Utilisateurs</a>
      <a href="{% url 'admin_orders' %}" class="admin-link">🛒 Commandes</a>
      <hr>
      <a href="/admin/" class="admin-link" target="_blank">🔧 Django Admin</a>
      <a href="{% url 'dashboard' %}" class="admin-link">← Dashboard user</a>
    </nav>
  </aside>
  <div class="admin-content">
    {% block admin_content %}{% endblock %}
  </div>
</div>
{% endblock %}

ÉTAPE 3 — Créer les templates admin_panel/

admin_panel/dashboard.html :
- 9 cartes stats en grid (listings en attente, ramassages non assignés, etc.)
- Section "Listings en attente" avec boutons Approuver/Rejeter inline
- Badge rouge sur le count "pending_review"

admin_panel/listings.html :
- Onglets de filtre : Tous / En attente / Approuvés / Rejetés / Vendus
- Table : photo miniature, titre, user, catégorie, valeur AI, date, statut
- Actions par ligne : bouton Approuver (vert) / Rejeter (rouge)
- Modal de rejet avec textarea "raison"

admin_panel/listing_detail.html :
- Photo grande du déchet
- Résultat analyse AI complet (JSON formaté lisiblement)
- Infos user (nom, email, téléphone)
- Gros boutons Approuver / Rejeter avec confirmation

admin_panel/pickups.html :
- Table : user, adresse, ville, date, créneau, statut, collecteur assigné
- Ligne "requested" mise en évidence (fond orange clair)
- Select dropdown collecteurs + bouton "Assigner" par ligne

admin_panel/users.html :
- Table : nom, email, rôle, actif/inactif, date inscription
- Toggle actif/inactif
- Select rôle modifiable

admin_panel/orders.html :
- Table : acheteur, vendeur, listing, montant, commission, statut, date

ÉTAPE 4 — Mettre à jour web/urls.py

from .views.admin_views import (
    AdminDashboardView, AdminListingsView, AdminReviewListingView,
    AdminPickupsView, AdminUsersView, AdminOrdersView
)

urlpatterns += [
    path('panel/', AdminDashboardView.as_view(), name='admin_panel'),
    path('panel/listings/', AdminListingsView.as_view(), name='admin_listings'),
    path('panel/listings/<uuid:pk>/', AdminReviewListingView.as_view(), name='admin_listing_detail'),
    path('panel/pickups/', AdminPickupsView.as_view(), name='admin_pickups'),
    path('panel/users/', AdminUsersView.as_view(), name='admin_users'),
    path('panel/orders/', AdminOrdersView.as_view(), name='admin_orders'),
]

Dis-moi quand c'est terminé.
```

---

## 9. Phase W8 — Academy & Blog

### Instructions pour Claude Code

```
Phase W7 validée. Passe à la Phase W8 : academy et blog.

ÉTAPE 1 — Créer web/views/academy_views.py et blog_views.py

# academy_views.py
from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from web.mixins import LoginRequiredMixin
from apps.academy.models import Course, Lesson, Enrollment, Certificate


class CourseListView(View):
    def get(self, request):
        courses = Course.objects.filter(is_published=True)
        user_enrollments = []
        if request.session.get('user_id'):
            user_enrollments = list(
                Enrollment.objects.filter(
                    user_id=request.session['user_id']
                ).values_list('course_id', flat=True)
            )
        return render(request, 'academy/list.html', {
            'courses': courses,
            'user_enrollments': user_enrollments,
        })


class CourseDetailView(View):
    def get(self, request, slug):
        course = get_object_or_404(Course, slug=slug, is_published=True)
        enrollment = None
        completed_lessons = []
        if request.session.get('user_id'):
            enrollment = Enrollment.objects.filter(
                user_id=request.session['user_id'], course=course
            ).first()
            if enrollment:
                completed_lessons = list(enrollment.completed_lessons.values_list('id', flat=True))
        return render(request, 'academy/detail.html', {
            'course': course,
            'lessons': course.lessons.all(),
            'enrollment': enrollment,
            'completed_lessons': completed_lessons,
        })


class EnrollCourseView(LoginRequiredMixin, View):
    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug)
        user = self.get_current_user(request)
        Enrollment.objects.get_or_create(user=user, course=course)
        messages.success(request, f'Inscrit au cours "{course.title}" !')
        return redirect('course_detail', slug=slug)


class CompleteLessonView(LoginRequiredMixin, View):
    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, pk=lesson_id)
        user = self.get_current_user(request)
        enrollment = get_object_or_404(Enrollment, user=user, course=lesson.course)
        enrollment.completed_lessons.add(lesson)
        total = lesson.course.lessons.count()
        completed = enrollment.completed_lessons.count()
        enrollment.progress_percent = int((completed / total) * 100) if total else 0
        if enrollment.progress_percent == 100:
            enrollment.is_completed = True
            enrollment.completed_at = timezone.now()
            Certificate.objects.get_or_create(user=user, course=lesson.course)
            messages.success(request, f'🎉 Cours complété ! Certificat obtenu.')
        enrollment.save()
        return redirect('course_detail', slug=lesson.course.slug)


# blog_views.py
from apps.blog.models import Post, BlogCategory

class BlogListView(View):
    def get(self, request):
        posts = Post.objects.filter(status='published').select_related('author', 'category')
        category_slug = request.GET.get('category', '')
        if category_slug:
            posts = posts.filter(category__slug=category_slug)
        Post.objects.filter(status='published').update(views=0)  # pas toucher au compteur ici
        return render(request, 'blog/list.html', {
            'posts': posts,
            'categories': BlogCategory.objects.all(),
            'active_category': category_slug,
        })


class BlogDetailView(View):
    def get(self, request, slug):
        post = get_object_or_404(Post, slug=slug, status='published')
        Post.objects.filter(pk=post.pk).update(views=post.views + 1)
        related = Post.objects.filter(
            status='published', category=post.category
        ).exclude(pk=post.pk)[:3]
        return render(request, 'blog/detail.html', {
            'post': post, 'related_posts': related
        })


ÉTAPE 2 — Créer les templates

academy/list.html :
- Grid de cards de cours
- Chaque card : thumbnail, titre, niveau (badge), durée, nb leçons, description courte
- Si enrolled : barre de progression + bouton "Continuer"
- Si pas enrolled : bouton "S'inscrire"

academy/detail.html :
- Header : thumbnail, titre, description, niveau, durée totale
- Barre de progression (si enrolled)
- Liste des leçons avec checkmark CSS si complétée
- Bouton "Commencer" ou "Continuer" (lien vers première leçon non complétée)
- Si complété : bouton "Télécharger le certificat" (PDF simple)

academy/lesson.html :
- Titre de la leçon
- Contenu en HTML ({{ lesson.content|safe }})
- Si video_url : iframe embed YouTube/Vimeo
- Bouton "Marquer comme complété" (form POST)
- Navigation : ← Leçon précédente | Leçon suivante →

blog/list.html :
- Header avec titre "Blog EcoCycle"
- Filtres par catégorie (boutons)
- Grid d'articles : image cover, catégorie, titre, extrait, auteur, date, temps de lecture
- Pagination

blog/detail.html :
- Image cover pleine largeur
- Titre, auteur, date, catégorie, temps de lecture
- Contenu complet ({{ post.content|safe }})
- Section "Articles similaires" (3 cards)

ÉTAPE 3 — Mettre à jour web/urls.py

from .views.academy_views import CourseListView, CourseDetailView, EnrollCourseView, CompleteLessonView
from .views.blog_views import BlogListView, BlogDetailView

urlpatterns += [
    path('academy/', CourseListView.as_view(), name='academy_list'),
    path('academy/<slug:slug>/', CourseDetailView.as_view(), name='course_detail'),
    path('academy/<slug:slug>/enroll/', EnrollCourseView.as_view(), name='enroll_course'),
    path('academy/lessons/<uuid:lesson_id>/complete/', CompleteLessonView.as_view(), name='complete_lesson'),
    path('blog/', BlogListView.as_view(), name='blog_list'),
    path('blog/<slug:slug>/', BlogDetailView.as_view(), name='blog_detail'),
]

Dis-moi quand c'est terminé.
```

---

## 10. Phase W9 — Finalisation & Polish

### Instructions pour Claude Code

```
Phase W8 validée. Phase finale W9 : polish, sécurité, performance.

ÉTAPE 1 — Messages flash dans base.html

Vérifie que le bloc messages est dans base.html avec ce style :
.messages-container { position fixed; top 80px; right 20px; z-index 9999; max-width 380px }
.alert { padding 14px 18px; border-radius 10px; margin-bottom 10px; display flex; justify-content space-between; box-shadow 0 4px 12px rgba(0,0,0,0.15) }
.alert-success { background #e8f5ee; border-left 4px solid #0d7a45; color #0d7a45 }
.alert-error { background #fef2f2; border-left 4px solid #ef4444; color #ef4444 }
.alert-warning { background #fff8e7; border-left 4px solid #f07c1a; color #f07c1a }
.alert-info { background #eff6ff; border-left 4px solid #3b82f6; color #3b82f6 }
.alert-close { background none; border none; cursor pointer; font-size 18px; color inherit }

Auto-dismiss après 5 secondes dans main.js :
setTimeout(() => {
  document.querySelectorAll('.alert').forEach(a => a.remove());
}, 5000);

ÉTAPE 2 — Pages d'erreur

templates/errors/404.html :
{% extends 'base.html' %}
{% block content %}
<div class="error-page">
  <span class="error-code">404</span>
  <h1>Page introuvable</h1>
  <p>La page que vous cherchez n'existe pas ou a été déplacée.</p>
  <a href="{% url 'home' %}" class="btn btn-primary">Retour à l'accueil</a>
</div>
{% endblock %}

templates/errors/500.html : même style, message "Erreur serveur interne"

Dans config/settings/base.py :
from django.conf.urls import handler404, handler500
# Dans config/urls.py :
handler404 = 'web.views.error_404'
handler500 = 'web.views.error_500'

Dans web/views/__init__.py :
from django.shortcuts import render
def error_404(request, exception):
    return render(request, 'errors/404.html', status=404)
def error_500(request):
    return render(request, 'errors/500.html', status=500)

ÉTAPE 3 — Cache sur les vues lourdes

Dans HomeView.get_context_data : cache les stats 5 minutes (déjà fait en W2).
Dans MarketplaceListView : cache la liste 2 minutes.
Dans PublicStatsView (API) : ajouter @cache_page(300).

ÉTAPE 4 — Sécurité web

Vérifie que :
- Tous les forms POST ont {% csrf_token %}
- Toutes les vues dashboard ont LoginRequiredMixin
- Toutes les vues admin_panel ont AdminRequiredMixin
- Les form d'enchère vérifient que l'user n'est pas le vendeur
- La session est flushée au logout

Dans config/settings/base.py, ajoute :
SESSION_COOKIE_AGE = 86400 * 7  # 7 jours
SESSION_COOKIE_HTTPONLY = True

ÉTAPE 5 — Menu hamburger mobile

Dans static/js/main.js, vérifie que ce code existe :
document.getElementById('hamburger').addEventListener('click', () => {
  document.querySelector('.nav-menu').classList.toggle('nav-open');
});

Dans main.css :
@media (max-width: 768px) {
  .nav-menu { display none; flex-direction column; position absolute; top 100%; left 0; right 0; background white; padding 20px; box-shadow 0 4px 20px rgba(0,0,0,0.1) }
  .nav-menu.nav-open { display flex }
  .hamburger { display block }
  .dashboard-layout { grid-template-columns 1fr }
  .sidebar { position static; height auto }
  .stats-grid { grid-template-columns repeat(2, 1fr) }
  .form-row { grid-template-columns 1fr }
  .auctions-grid { grid-template-columns 1fr }
}

ÉTAPE 6 — Vérifications finales

Lance :
python manage.py check
python manage.py check --deploy

Corrige tous les warnings.

Lance le serveur et teste le flux complet :
1. Inscription → email de vérification (affiché dans console en dev)
2. Login → dashboard
3. Soumettre un déchet avec photo → analyse AI → listing créé
4. Aller sur /panel/ (connecté en admin) → voir le listing en attente
5. Approuver le listing → notification créée
6. Marketplace → voir le listing approuvé comme auction
7. Placer une enchère
8. Vérifier les messages flash à chaque étape

Liste tous les fichiers modifiés/créés.
Dis-moi si des erreurs subsistent.
```

---

## 11. Charte Graphique

```css
/* Couleurs principales — à utiliser dans tous les templates */
--color-primary: #0d7a45;       /* Vert EcoCycle */
--color-secondary: #f07c1a;     /* Orange EcoCycle */
--color-dark: #1a1a2e;          /* Fond sombre */
--color-cream: #f5f0e8;         /* Fond crème */
--color-light-green: #e8f5ee;   /* Vert pâle */
--color-gray: #666666;          /* Texte secondaire */

/* Typographie */
--font-heading: 'Syne', sans-serif;
--font-body: 'DM Sans', sans-serif;

/* Spacing */
--radius-sm: 8px;
--radius-md: 12px;
--radius-lg: 16px;

/* Shadows */
--shadow-card: 0 4px 16px rgba(0, 0, 0, 0.08);
--shadow-hover: 0 8px 32px rgba(13, 122, 69, 0.15);

/* Statuts */
--status-draft: #9ca3af;
--status-pending: #f07c1a;
--status-approved: #0d7a45;
--status-sold: #3b82f6;
--status-rejected: #ef4444;
--status-completed: #10b981;
```

---

## 12. Mixins & Utilitaires Réutilisables

Ces éléments sont utilisés dans plusieurs phases. Claude Code doit les créer une seule fois en Phase W1.

### web/mixins.py — complet

```python
from django.shortcuts import redirect
from django.contrib import messages
from apps.accounts.models import User


class LoginRequiredMixin:
    """Vérifie que l'utilisateur est connecté via session."""
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('user_id'):
            messages.error(request, 'Connectez-vous pour accéder à cette page.')
            return redirect(f'/login/?next={request.path}')
        return super().dispatch(request, *args, **kwargs)

    def get_current_user(self, request):
        try:
            return User.objects.get(id=request.session['user_id'])
        except (User.DoesNotExist, KeyError):
            request.session.flush()
            return None


class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if hasattr(response, 'status_code') and response.status_code == 302:
            return response
        if request.session.get('user_role') != 'admin':
            messages.error(request, 'Accès réservé aux administrateurs.')
            return redirect('dashboard')
        return response


class CollectorRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if hasattr(response, 'status_code') and response.status_code == 302:
            return response
        if request.session.get('user_role') not in ['collector', 'admin']:
            messages.error(request, 'Accès réservé aux collecteurs.')
            return redirect('dashboard')
        return response
```

---

## Résumé des URLs finales

```
/                           → home (landing page)
/login/                     → connexion
/register/                  → inscription
/logout/                    → déconnexion
/verify-email/<token>/      → vérification email
/reset-password/            → mot de passe oublié
/reset-password/confirm/<token>/ → réinitialisation

/dashboard/                 → vue d'ensemble utilisateur
/dashboard/listings/        → mes déchets
/dashboard/listings/submit/ → soumettre un déchet
/dashboard/orders/          → mes commandes
/dashboard/impact/          → mon impact CO2
/dashboard/pickups/         → mes ramassages
/dashboard/pickups/request/ → nouvelle demande
/dashboard/pickups/<id>/    → détail ramassage
/dashboard/profile/         → mon profil

/marketplace/               → liste enchères (public)
/marketplace/<id>/          → détail enchère (public)
/marketplace/<id>/bid/      → placer une enchère (AJAX)
/marketplace/<id>/buy-now/  → achat immédiat

/panel/                     → admin dashboard
/panel/listings/            → admin listings
/panel/listings/<id>/       → admin listing detail
/panel/pickups/             → admin ramassages
/panel/users/               → admin utilisateurs
/panel/orders/              → admin commandes

/academy/                   → liste cours
/academy/<slug>/            → détail cours
/academy/<slug>/enroll/     → s'inscrire
/academy/lessons/<id>/complete/ → compléter leçon

/blog/                      → liste articles
/blog/<slug>/               → article complet

/contact/                   → form contact (POST)
/newsletter/subscribe/      → inscription newsletter
/newsletter/confirm/<token>/ → confirmation newsletter
```

---

*Prompt généré pour le projet EcoCycle Haiti — Eliézer Léonce — 2026*
