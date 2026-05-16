# EcoCycle Haiti — Plateforme de Recyclage Intelligent

API REST Django + Interface Web pour la plateforme de recyclage intelligent EcoCycle Haiti. Connecte les citoyens haïtiens aux collecteurs agréés, transforme les déchets en opportunités économiques via des enchères, et propulse l'économie circulaire d'Haïti grâce à l'IA.

## Stack technique

- **Django 5.1.4** + **Django REST Framework 3.15.2**
- **Django Templates** — interface web complète (sessions, pas JWT)
- **PostgreSQL** (prod) / SQLite (dev)
- **Celery 5.4.0** + **Redis** — tâches asynchrones et planifiées
- **JWT** via `djangorestframework-simplejwt` — pour l'app mobile Flutter
- **Sessions Django** — authentification pour l'interface web
- **Stockage médias** — volume local Railway (fichiers vidéo, thumbnails, avatars)
- **Claude Vision API** (Anthropic) — analyse IA des déchets par photo
- **Resend** — emails transactionnels (certificats, contact, newsletter)
- **Firebase FCM** — notifications push
- **Whitenoise** + **Gunicorn gthread** — fichiers statiques et serveur WSGI
- Déploiement sur **Railway** (5 services : web, celery-worker, celery-beat, Redis, PostgreSQL)

## Architecture

```
ecocycle/
├── apps/
│   ├── accounts/       # Utilisateurs (UUID, email auth, rôles: user/collector/admin)
│   ├── waste/          # Annonces de déchets + analyse IA Claude Vision
│   ├── marketplace/    # Enchères et achats immédiats
│   ├── collections/    # Demandes de ramassage physique
│   ├── notifications/  # Notifications DB + email (Resend) + push (FCM) + tâches Celery
│   ├── impact/         # CO2 économisé, leaderboard
│   ├── academy/        # Cours, leçons multi-vidéos, inscriptions, certificats PDF
│   ├── blog/           # Articles
│   └── core/           # Contact, newsletter, SiteConfiguration
├── web/                # Interface web (Django Templates + sessions)
│   ├── views/
│   │   ├── auth_views.py       # Connexion / inscription / déconnexion
│   │   ├── dashboard_views.py  # Dashboard utilisateur
│   │   ├── academy_views.py    # Cours, leçons, inscriptions, certificats
│   │   ├── admin_views.py      # Panel admin complet
│   │   └── page_views.py       # Pages publiques
│   └── urls.py
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── celery.py
│   └── urls.py
├── templates/
│   ├── base.html
│   ├── pages/                  # comment_ca_marche, fonctionnalites, notre_impact, faq, contact
│   ├── auth/                   # login, register, reset password, verify email
│   ├── dashboard/              # overview, listings, orders, impact, pickups, profile, certificates
│   ├── marketplace/
│   ├── academy/                # list, detail, lesson_detail
│   ├── blog/
│   ├── admin_panel/            # dashboard, listings, users, orders, pickups, blog, academy, config…
│   └── emails/                 # certificate_earned, admin_course_completed, contact_alert…
├── static/
│   ├── css/main.css
│   ├── css/dashboard.css
│   └── js/main.js
├── railway.toml                # Service web (Gunicorn)
├── railway-celery.toml         # Service Celery worker
└── railway-beat.toml           # Service Celery Beat (tâches planifiées)
```

## Interface web

### Pages publiques

| URL | Page |
|---|---|
| `/` | Accueil — Hero, stats live, marketplace teaser, slider admin |
| `/comment-ca-marche/` | Fonctionnement étape par étape |
| `/fonctionnalites/` | Grille de fonctionnalités + app mobile |
| `/notre-impact/` | Statistiques live (DB) + témoignages |
| `/faq/` | Accordion FAQ |
| `/contact/` | Formulaire de contact (email async Celery) |
| `/marketplace/` | Enchères publiques |
| `/academy/` | Catalogue de cours |
| `/blog/` | Articles |

### Dashboard utilisateur

| URL | Page |
|---|---|
| `/dashboard/` | Vue d'ensemble |
| `/dashboard/listings/` | Mes déchets soumis |
| `/dashboard/listings/submit/` | Soumettre un déchet (analyse IA) |
| `/dashboard/pickups/` | Mes demandes de ramassage |
| `/dashboard/pickups/request/` | Nouvelle demande |
| `/dashboard/pickups/<id>/` | Détail ramassage + timeline statut |
| `/dashboard/orders/` | Mes commandes |
| `/dashboard/impact/` | Mon impact environnemental |
| `/dashboard/certificates/` | Mes certificats + téléchargement PDF |
| `/dashboard/profile/` | Mon profil |
| `/academy/<slug>/` | Détail cours (inscription) |
| `/academy/<slug>/lessons/<id>/` | Lecteur leçon (vidéo + contenu + nav + mark-complete) |

### Dashboard collecteur

| URL | Page |
|---|---|
| `/collector/` | Dashboard collecteur |
| `/collector/pickups/` | Collectes assignées |
| `/collector/pickups/<id>/` | Détail + mise à jour statut |
| `/collector/profile/` | Profil collecteur |

### Panel admin

| URL | Page |
|---|---|
| `/panel/` | Dashboard admin (stats, KPIs) |
| `/panel/listings/` | Toutes les annonces |
| `/panel/listings/<id>/` | Revue / approbation annonce |
| `/panel/pickups/` | Tous les ramassages |
| `/panel/pickups/<id>/` | Détail + assignation collecteur |
| `/panel/users/` | Gestion utilisateurs |
| `/panel/users/<id>/` | Détail utilisateur |
| `/panel/orders/` | Toutes les commandes |
| `/panel/orders/<id>/` | Détail commande |
| `/panel/blog/` | Gestion articles |
| `/panel/blog/create/` | Créer un article |
| `/panel/blog/<id>/edit/` | Éditer un article |
| `/panel/blog/categories/` | Catégories blog |
| `/panel/academy/` | Gestion cours |
| `/panel/academy/create/` | Créer un cours |
| `/panel/academy/<id>/` | Détail cours + liste leçons |
| `/panel/academy/<course_id>/lessons/create/` | Créer leçon + première vidéo |
| `/panel/academy/<course_id>/lessons/<id>/edit/` | Éditer leçon + CRUD vidéos |
| `/panel/academy/enrollments/` | Toutes les inscriptions |
| `/panel/academy/certificates/` | Tous les certificats + PDF |
| `/panel/newsletters/` | Abonnés newsletter |
| `/panel/contacts/` | Messages de contact |
| `/panel/config/` | Configuration du site (SiteConfiguration) |
| `/panel/sliders/` | Slides de la page d'accueil |

## Academy — e-learning

Le module Academy gère des cours structurés en leçons multi-vidéos.

**Modèles :**
- `Course` : titre, description, niveau, thumbnail, is_free, is_published, durée auto-calculée
- `Lesson` : titre, contenu Markdown, ordre, durée auto-calculée (somme des vidéos)
- `LessonVideo` : fichier MP4/WebM **ou** URL externe (YouTube, Vimeo, autre), embed automatique
- `Enrollment` : progression par leçon, `progress_percent`, `is_completed`
- `Certificate` : délivré automatiquement à 100% de progression, PDF téléchargeable

**Flux completion :**
```
User mark-complete dernière leçon
  → Enrollment.update_progress()
  → 100% → Certificate créé
  → Celery task: email certificat au user + notification admins
```

## API REST

L'API (`/api/`) est destinée à l'application mobile Flutter et utilise JWT.

### Authentification — `/api/auth/`

| Méthode | Endpoint | Description |
|---|---|---|
| POST | `/register/` | Inscription |
| POST | `/login/` | Connexion |
| POST | `/logout/` | Déconnexion (blacklist refresh token) |
| GET/PATCH | `/profile/` | Profil utilisateur |
| POST | `/change-password/` | Changement de mot de passe |
| POST | `/reset-password/` | Demande de réinitialisation |
| POST | `/reset-password/confirm/` | Confirmation avec token |
| POST | `/verify-email/<token>/` | Vérification email |
| PATCH | `/fcm-token/` | Mise à jour token push |

### Déchets — `/api/waste/`

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/categories/` | Liste des catégories (public) |
| GET/POST | `/listings/` | Annonces de déchets |
| GET/PATCH | `/listings/<id>/` | Détail / modification |
| POST | `/analyze/` | Analyse IA par photo |
| GET | `/admin/listings/` | Toutes les annonces (admin) |
| POST | `/admin/listings/<id>/review/` | Approuver / rejeter (admin) |

### Marketplace — `/api/marketplace/`

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/auctions/` | Enchères actives (public) |
| POST | `/auctions/create/` | Créer une enchère |
| GET | `/auctions/<id>/` | Détail enchère |
| POST | `/auctions/<id>/bid/` | Placer une enchère |
| POST | `/auctions/<id>/buy-now/` | Achat immédiat |
| GET | `/orders/my/` | Mes commandes |
| GET | `/orders/sales/` | Mes ventes |

### Ramassage — `/api/collections/`

| Méthode | Endpoint | Description |
|---|---|---|
| GET/POST | `/` | Demandes de ramassage |
| GET | `/admin/` | Toutes les demandes (admin) |
| GET | `/collector/` | Collectes assignées (collecteur) |
| GET | `/<id>/` | Détail ramassage |
| POST | `/<id>/assign/` | Assigner un collecteur (admin) |
| PATCH | `/<id>/status/` | Mettre à jour le statut |

### Autres modules

| Préfixe | Module |
|---|---|
| `/api/notifications/` | Notifications (liste, marquer lu) |
| `/api/impact/` | Stats CO2, leaderboard |
| `/api/academy/` | Cours, leçons, inscriptions, certificats |
| `/api/blog/` | Articles et catégories |
| `/api/contact/` | Formulaire de contact |
| `/api/newsletter/` | Abonnement newsletter (double opt-in) |

## Tâches asynchrones (Celery)

### Tâches planifiées

| Tâche | Fréquence |
|---|---|
| Clôture des enchères expirées | Toutes les 5 minutes |
| Annulation des ramassages non assignés après 72h | Toutes les heures |
| Rapport hebdomadaire admin | Lundi 8h (heure Haïti) |

### Tâches déclenchées par événement

| Tâche | Déclencheur |
|---|---|
| `notify_course_completed` | Utilisateur termine un cours → email certificat + alerte admins |
| `notify_contact_message` | Formulaire de contact soumis → alerte admins |
| `notify_newsletter_signup` | Inscription newsletter → email confirmation double opt-in |

```bash
# Lancer en développement
celery -A config worker --loglevel=info   # terminal 2
celery -A config beat --loglevel=info     # terminal 3
```

## Déploiement Railway

Trois services définis :

| Fichier | Service | Commande |
|---|---|---|
| `railway.toml` | Web (Gunicorn) | `migrate` + `init_site.py` + `gunicorn gthread` |
| `railway-celery.toml` | Celery Worker | `celery -A config worker` |
| `railway-beat.toml` | Celery Beat | `celery -A config beat --scheduler DatabaseScheduler` |

```bash
# 1. Créer un projet Railway avec PostgreSQL + Redis
# 2. Connecter le dépôt GitHub
# 3. Ajouter les variables d'environnement (voir ci-dessous)
# 4. Déployer le service web (railway.toml)
# 5. Créer un second service pointant sur railway-celery.toml
# 6. Créer un troisième service pointant sur railway-beat.toml
# 7. Seeder les catégories de déchets
railway run python manage.py seed_waste_categories
```

Le superutilisateur est créé automatiquement au démarrage via `init_site.py` (variables `ADMIN_EMAIL` / `ADMIN_PASSWORD`).

## Installation locale

**Prérequis :** Python 3.11+, Redis (optionnel en dev)

```bash
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Éditer .env

python manage.py migrate
python manage.py seed_waste_categories
python init_site.py

python manage.py runserver
```

Interface web : `http://localhost:8000` — API : `http://localhost:8000/api/`

## Variables d'environnement

| Variable | Requis | Description |
|---|---|---|
| `SECRET_KEY` | Oui | Clé secrète Django (50+ caractères) |
| `DATABASE_URL` | Oui | URL PostgreSQL (Railway la génère automatiquement) |
| `REDIS_URL` | Oui | URL Redis (Railway la génère automatiquement) |
| `RESEND_API_KEY` | Oui | Clé API Resend (emails transactionnels) |
| `ANTHROPIC_API_KEY` | Oui | Clé API Anthropic (analyse IA photo déchets) |
| `FIREBASE_CREDENTIALS_B64` | Oui | JSON Firebase encodé en base64 (push) |
| `ALLOWED_HOSTS` | Prod | Domaines autorisés, séparés par virgule |
| `FRONTEND_URL` | Non | URL du frontend (défaut : `http://localhost:8000`) |
| `ADMIN_EMAIL` | Non | Email admin (défaut : `admin@ecocycle.ht`) |
| `ADMIN_PASSWORD` | Non | Mot de passe admin initial |
| `RESEND_FROM_EMAIL` | Non | Expéditeur email (défaut : `noreply@ecocycle.ht`) |

```bash
# Encoder les credentials Firebase
base64 -i firebase-credentials.json | tr -d '\n'
# Coller la sortie dans FIREBASE_CREDENTIALS_B64
```

## Modèles de données principaux

```
User (UUID, email, rôle: user/collector/admin)
├── WasteListing (photo, analyse IA, statut) → Auction → Bid / Order → ImpactRecord
├── PickupRequest (statut, historique JSON) → ImpactRecord
├── Enrollment → LessonProgress → Certificate (PDF)
└── UserImpactSummary (CO2 total, rang communauté)

Course → Lesson → LessonVideo (fichier ou URL YouTube/Vimeo)
SiteConfiguration (singleton: slider, liens app, contact)
```

## Flux principal

```
Photo mobile / web
  → POST /api/waste/analyze/ (analyse IA Claude Vision)
  → POST /api/waste/listings/ (draft)
  → Admin approuve → statut: approved
  → Création Auction sur le marketplace
  → Enchère gagnante / achat immédiat → Order
  → Tâche Celery: ImpactRecord (CO2 calculé) + notifications
```

## Catégories de déchets

| Catégorie | Slug | Prix de base (HTG/kg) |
|---|---|---|
| Plastique | `plastic` | 50 |
| Métal | `metal` | 120 |
| Papier/Carton | `paper` | 30 |
| Électronique | `electronics` | 500 |
| Verre | `glass` | 20 |
| Pneus | `tires` | 80 |
| Autre | `other` | 10 |

## Sécurité

- JWT avec rotation des refresh tokens et blacklist (API Flutter)
- Sessions Django sécurisées (interface web)
- HTTPS forcé en production (`SECURE_SSL_REDIRECT`) + HSTS 1 an
- Headers : `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, XSS filter
- Throttling API : 100 req/jour (anonyme), 1000 req/jour (authentifié), 20 req/heure (analyse IA)
- Noms d'URL distincts entre API (`apps/*/urls.py`) et web (`web/urls.py`) pour éviter les conflits de résolution `{% url %}`

## Licence

Projet propriétaire — EcoCycle Haiti © 2026. Créé par Eliézer Léonce, Valcin Vaillant et Lafleur.
