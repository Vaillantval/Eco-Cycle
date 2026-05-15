# EcoCycle Haiti — API Backend

API REST Django pour la plateforme de recyclage intelligent EcoCycle Haiti. Conçue pour alimenter l'application mobile Flutter, elle connecte les citoyens haïtiens aux collecteurs agréés et transforme les déchets en opportunités économiques.

## Stack technique

- **Django 5.1.4** + **Django REST Framework 3.15.2**
- **PostgreSQL** (prod) / SQLite (dev)
- **Celery 5.4.0** + **Redis** — tâches asynchrones et planifiées
- **JWT** via `djangorestframework-simplejwt` (1h access / 30j refresh)
- **Cloudinary** — stockage des photos de déchets
- **Claude Vision API** (Anthropic) — analyse IA des déchets par photo
- **Resend** — emails transactionnels
- **Firebase FCM** — notifications push
- **Whitenoise** + **Gunicorn** — fichiers statiques et serveur WSGI
- Déploiement sur **Railway**

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
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── celery.py
│   └── urls.py
└── templates/emails/   # 8 templates HTML
```

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
python manage.py createsuperuser

# Serveur de développement
python manage.py runserver
```

L'API est disponible sur `http://localhost:8000`.

## Variables d'environnement

Copier `.env.example` en `.env` et renseigner :

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

### Encoder les credentials Firebase pour Railway

```bash
base64 -i firebase-credentials.json | tr -d '\n'
# Coller la sortie dans FIREBASE_CREDENTIALS_B64
```

## Endpoints API

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
| POST | `/listings/<id>/analyze/` | Déclencher l'analyse IA |
| POST | `/listings/<id>/approve/` | Approuver (admin) |
| POST | `/listings/<id>/reject/` | Rejeter (admin) |

### Marketplace — `/api/marketplace/`

| Méthode | Endpoint | Description |
|---|---|---|
| GET/POST | `/auctions/` | Enchères actives |
| POST | `/auctions/<id>/bid/` | Placer une enchère |
| POST | `/auctions/<id>/buy-now/` | Achat immédiat |
| GET | `/orders/` | Mes commandes |

### Ramassage — `/api/collections/`

| Méthode | Endpoint | Description |
|---|---|---|
| GET/POST | `/pickups/` | Demandes de ramassage |
| POST | `/pickups/<id>/assign/` | Assigner un collecteur (admin) |
| POST | `/pickups/<id>/status/` | Mettre à jour le statut |

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

17 tâches enregistrées, 3 tâches périodiques :

| Tâche | Fréquence |
|---|---|
| Clôture des enchères expirées | Toutes les 5 minutes |
| Annulation des ramassages non assignés après 72h | Toutes les heures |
| Rapport hebdomadaire admin | Lundi 8h (heure Haïti) |

### Lancer Celery en développement

```bash
# Worker (terminal 2)
celery -A config worker --loglevel=info

# Beat / planificateur (terminal 3)
celery -A config beat --loglevel=info
```

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
Photo mobile
    → POST /api/waste/listings/ (draft)
    → Tâche Celery: Claude Vision analyse la photo
    → Admin approuve → statut: approved
    → Création Auction sur le marketplace
    → Enchère gagnante / achat immédiat → Order
    → Tâche Celery: ImpactRecord (CO2 calculé)
    → Notifications email + push
```

## Déploiement Railway

Le projet est préconfiguré pour Railway.

```bash
# 1. Créer un projet Railway avec PostgreSQL + Redis
# 2. Connecter le dépôt GitHub
# 3. Ajouter les variables d'environnement dans le dashboard
# 4. Railway exécute automatiquement :
#    pip install -r requirements.txt
#    python manage.py collectstatic --noinput
#    python manage.py migrate
```

Les services sont définis dans `railway.toml` : `web`, `celery-worker`, `postgres`, `redis`.

En production, penser à :

```bash
# Créer le superutilisateur via Railway CLI
railway run python manage.py createsuperuser

# Seeder les catégories de déchets
railway run python manage.py seed_waste_categories
```

## Catégories de déchets pré-configurées

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

- JWT avec rotation des refresh tokens et blacklist
- HTTPS forcé en production (`SECURE_SSL_REDIRECT`)
- HSTS 1 an avec preload
- Headers sécurité : `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, XSS filter
- Throttling API : 100 req/jour (anonyme), 1000 req/jour (authentifié), 20 req/heure (analyse IA)
- Mots de passe validés par Django (longueur, complexité, communs)

## Licence

Projet propriétaire — EcoCycle Haiti © 2026
