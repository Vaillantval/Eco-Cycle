# EcoCycle Haiti — Plateforme de Recyclage Intelligent

API REST Django + Interface Web pour la plateforme de recyclage intelligent EcoCycle Haiti. Connecte les citoyens haïtiens aux collecteurs agréés, transforme les déchets en opportunités économiques via des enchères, et propulse l'économie circulaire d'Haïti grâce à l'IA.

## Stack technique

- **Django 5.1.4** + **Django REST Framework 3.15.2**
- **Django Templates** — interface web complète (sessions, pas JWT)
- **PostgreSQL** (prod) / SQLite (dev)
- **Celery 5.4.0** + **Redis** — tâches asynchrones et planifiées
- **JWT** via `djangorestframework-simplejwt` — pour l'app mobile Flutter
- **Sessions Django** — authentification pour l'interface web
- **Cloudinary** — stockage des photos de déchets
- **Claude Vision API** (Anthropic `>=0.49.0`) — analyse IA des déchets par photo
- **Resend** — emails transactionnels
- **Firebase FCM** — notifications push
- **Whitenoise** + **Gunicorn gthread** — fichiers statiques et serveur WSGI
- Déploiement sur **Railway** (web + celery-worker)

## Architecture

```
ecocycle/
├── apps/
│   ├── accounts/       # Utilisateurs (UUID, email auth, rôles)
│   ├── waste/          # Annonces de déchets + analyse IA
│   ├── marketplace/    # Enchères et achats immédiats
│   ├── collections/    # Demandes de ramassage physique
│   ├── notifications/  # Notifications DB + email + push
│   ├── impact/         # CO2 économisé, leaderboard
│   ├── academy/        # Cours et certificats
│   ├── blog/           # Articles
│   └── core/           # Contact, newsletter
├── web/                # Interface web (vues Django Templates)
│   ├── views/
│   │   ├── auth_views.py       # Connexion / inscription / déconnexion
│   │   ├── dashboard_views.py  # Dashboard utilisateur / collecteur / admin
│   │   └── page_views.py       # Pages publiques statiques
│   └── urls.py
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── celery.py
│   └── urls.py
├── templates/
│   ├── base.html               # Layout principal avec navbar dropdown
│   ├── home.html               # Page d'accueil (Hero + Stats + Marketplace)
│   ├── pages/                  # Pages publiques dédiées
│   │   ├── comment_ca_marche.html
│   │   ├── fonctionnalites.html
│   │   ├── notre_impact.html
│   │   ├── faq.html
│   │   └── contact.html
│   ├── auth/                   # Login, register
│   ├── dashboard/              # Dashboard et sous-pages
│   ├── marketplace/            # Marketplace web
│   ├── academy/                # Cours web
│   └── blog/                   # Blog web
├── static/
│   ├── css/
│   │   ├── main.css            # Styles globaux + navbar + hero
│   │   └── dashboard.css       # Styles dashboard
│   └── js/main.js
├── railway.toml                # Service web
└── railway-celery.toml         # Service Celery worker
```

## Interface web

L'interface web (`/`) utilise les sessions Django (indépendante du JWT Flutter). Elle inclut :

**Navigation** — Navbar fixe avec menus dropdown hover (La Plateforme, Apprendre) + menu mobile overlay.

**Pages publiques**

| URL | Page |
|---|---|
| `/` | Accueil — Hero, stats live, marketplace teaser |
| `/comment-ca-marche/` | Fonctionnement étape par étape |
| `/fonctionnalites/` | Grille de fonctionnalités + app mobile |
| `/notre-impact/` | Statistiques live (DB) + témoignages |
| `/faq/` | Accordion FAQ + teaser contact |
| `/contact/` | Formulaire de contact (GET/POST) |
| `/marketplace/` | Enchères publiques |
| `/academy/` | Cours disponibles |
| `/blog/` | Articles |

**Dashboard utilisateur**

| URL | Page |
|---|---|
| `/dashboard/` | Vue d'ensemble |
| `/dashboard/listings/` | Mes déchets soumis |
| `/dashboard/listings/submit/` | Soumettre un déchet (analyse IA) |
| `/dashboard/pickups/` | Mes demandes de ramassage |
| `/dashboard/pickups/<id>/` | Détail ramassage + timeline statut |
| `/dashboard/impact/` | Mon impact environnemental + progression |
| `/dashboard/orders/` | Mes commandes |
| `/dashboard/profile/` | Mon profil |
| `/dashboard/academy/` | Mes formations |
| `/dashboard/blog/` | Blog |

**Dashboard collecteur** — liste de collectes assignées, mise à jour statuts.

**Panel admin** — gestion des annonces, utilisateurs, ramassages, commandes.

## API REST

L'API REST (`/api/`) est destinée à l'application mobile Flutter et utilise JWT.

### Authentification — `/api/auth/`

| Méthode | Endpoint | Description |
|---|---|---|
| POST | `/register/` | Inscription (retourne JWT immédiatement) |
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

## Installation locale

**Prérequis :** Python 3.11+, Redis (optionnel en dev)

```bash
# Cloner et créer le venv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dépendances
pip install -r requirements.txt

# Variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs (voir section Variables d'environnement)

# Migrations et données initiales
python manage.py migrate
python manage.py seed_waste_categories

# Superutilisateur
python init_site.py  # ou manage.py createsuperuser

# Serveur de développement
python manage.py runserver
```

L'interface web est sur `http://localhost:8000`, l'API sur `http://localhost:8000/api/`.

## Variables d'environnement

| Variable | Requis | Description |
|---|---|---|
| `SECRET_KEY` | Oui | Clé secrète Django (50+ caractères) |
| `DATABASE_URL` | Oui | URL PostgreSQL (Railway la génère automatiquement) |
| `REDIS_URL` | Oui | URL Redis (Railway la génère automatiquement) |
| `CLOUDINARY_CLOUD_NAME` | Oui | Nom du cloud Cloudinary |
| `CLOUDINARY_API_KEY` | Oui | Clé API Cloudinary |
| `CLOUDINARY_API_SECRET` | Oui | Secret Cloudinary |
| `RESEND_API_KEY` | Oui | Clé API Resend (emails) |
| `ANTHROPIC_API_KEY` | Oui | Clé API Anthropic (analyse IA) |
| `FIREBASE_CREDENTIALS_B64` | Oui | JSON Firebase encodé en base64 (push) |
| `ALLOWED_HOSTS` | Prod | Domaines autorisés, séparés par virgule |
| `FRONTEND_URL` | Non | URL du frontend (défaut : `http://localhost:8000`) |
| `ADMIN_EMAIL` | Non | Email admin (défaut : `admin@ecocycle.ht`) |

```bash
# Encoder les credentials Firebase pour Railway
base64 -i firebase-credentials.json | tr -d '\n'
# Coller la sortie dans FIREBASE_CREDENTIALS_B64
```

## Tâches asynchrones (Celery)

| Tâche | Fréquence |
|---|---|
| Clôture des enchères expirées | Toutes les 5 minutes |
| Annulation des ramassages non assignés après 72h | Toutes les heures |
| Rapport hebdomadaire admin | Lundi 8h (heure Haïti) |

```bash
# Lancer en développement
celery -A config worker --loglevel=info   # terminal 2
celery -A config beat --loglevel=info     # terminal 3
```

## Déploiement Railway

Deux services définis :

| Fichier | Service | Commande |
|---|---|---|
| `railway.toml` | Web (Gunicorn) | `migrate` + `init_site.py` + `gunicorn gthread` |
| `railway-celery.toml` | Celery Worker | `celery -A config worker` |

```bash
# 1. Créer un projet Railway avec PostgreSQL + Redis
# 2. Connecter le dépôt GitHub
# 3. Ajouter les variables d'environnement dans le dashboard Railway
# 4. Déployer le service web (railway.toml)
# 5. Créer un second service "celery-worker" pointant sur railway-celery.toml
# 6. Seeder les catégories
railway run python manage.py seed_waste_categories
```

Le superutilisateur est créé automatiquement au démarrage via `init_site.py` (variables `ADMIN_EMAIL` / `ADMIN_PASSWORD`).

## Modèles de données principaux

```
User (UUID, email, rôle: user/collector/admin)
├── WasteListing (photo, analyse IA, statut)
│   └── Auction → Bid / Order → ImpactRecord
├── PickupRequest (statut, historique JSON) → ImpactRecord
├── Enrollment → Certificate
└── UserImpactSummary (CO2 total, rang communauté)
```

## Flux principal

```
Photo mobile / web
    → POST /api/waste/analyze/ (analyse IA Claude Vision)
    → POST /api/waste/listings/ (draft)
    → Admin approuve → statut: approved
    → Création Auction sur le marketplace
    → Enchère gagnante / achat immédiat → Order
    → Tâche Celery: ImpactRecord (CO2 calculé)
    → Notifications email + push FCM
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
- Mots de passe validés par Django (longueur, complexité)
- Noms d'URL séparés entre API (`/api/`) et web (templates) pour éviter les conflits de résolution

## Licence

Projet propriétaire — EcoCycle Haiti © 2026. Créé par Eliézer Léonce, Valcin Vaillant et Lafleur.
