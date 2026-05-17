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
- **Resend** — emails transactionnels (certificats, contact, newsletter, paiements)
- **Firebase FCM** — notifications push
- **Stripe** (`stripe==15.1.0`) — paiement par carte bancaire
- **PlopPlop** — passerelle de paiement haïtienne (MonCash, NatCash, Kashpaw)
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
│   ├── payments/       # Service de paiement (Stripe + PlopPlop + Transaction model)
│   ├── notifications/  # Notifications DB + email (Resend) + push (FCM) + tâches Celery
│   ├── impact/         # CO2 économisé, leaderboard
│   ├── academy/        # Cours (gratuits ou payants), leçons, inscriptions, certificats PDF
│   ├── blog/           # Articles
│   └── core/           # Contact, newsletter, SiteConfiguration
├── web/                # Interface web (Django Templates + sessions)
│   ├── views/
│   │   ├── auth_views.py       # Connexion / inscription / déconnexion
│   │   ├── dashboard_views.py  # Dashboard utilisateur
│   │   ├── academy_views.py    # Cours, leçons, inscriptions, paiement cours
│   │   ├── payment_views.py    # Checkout, Stripe, PlopPlop, webhooks
│   │   ├── marketplace_views.py # Marketplace web, enchères, achat immédiat
│   │   ├── admin_views.py      # Panel admin complet
│   │   └── page_views.py       # Pages publiques
│   └── urls.py
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── celery.py
│   └── urls.py             # Inclut les webhooks paiement (CSRF-exempt)
├── templates/
│   ├── base.html
│   ├── pages/                  # comment_ca_marche, fonctionnalites, notre_impact, faq, contact
│   ├── auth/                   # login, register, reset password, verify email
│   ├── dashboard/              # overview, listings, orders, impact, pickups, profile, certificates
│   ├── marketplace/            # list, detail (countdown, bid/buynow conditionnels)
│   ├── payments/               # checkout, stripe_checkout, success, course_checkout, course_success…
│   ├── academy/                # list, detail, lesson_detail
│   ├── blog/
│   ├── admin_panel/            # dashboard, listings, users, orders, auctions, pickups, blog, academy…
│   └── emails/                 # certificate_earned, order_confirmation, order_paid_seller,
│                               # course_enrollment_confirmation, contact_alert…
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
| `/marketplace/` | Enchères publiques (filtres, tri, countdown, badges type) |
| `/academy/` | Catalogue de cours (gratuits et payants) |
| `/blog/` | Articles |

### Dashboard utilisateur

| URL | Page |
|---|---|
| `/dashboard/` | Vue d'ensemble (widget enchères actives avec countdown live) |
| `/dashboard/listings/` | Mes déchets soumis (avec colonne enchère + statut) |
| `/dashboard/listings/submit/` | Soumettre un déchet (analyse IA) |
| `/dashboard/pickups/` | Mes demandes de ramassage |
| `/dashboard/pickups/request/` | Nouvelle demande |
| `/dashboard/pickups/<id>/` | Détail ramassage + timeline statut |
| `/dashboard/orders/` | Mes commandes (acheteur) |
| `/dashboard/impact/` | Mon impact environnemental |
| `/dashboard/certificates/` | Mes certificats + téléchargement PDF |
| `/dashboard/profile/` | Mon profil |
| `/academy/<slug>/` | Détail cours (inscription / paiement) |
| `/academy/<slug>/lessons/<id>/` | Lecteur leçon (vidéo + contenu + nav + mark-complete) |

### Dashboard collecteur

| URL | Page |
|---|---|
| `/collector/` | Dashboard collecteur |
| `/collector/pickups/` | Collectes assignées |
| `/collector/pickups/<id>/` | Détail + mise à jour statut |
| `/collector/profile/` | Profil collecteur |

### Paiement

| URL | Description |
|---|---|
| `/payment/<order_id>/` | Choix du mode de paiement (commande marketplace) |
| `/payment/<order_id>/stripe/init/` | Création du PaymentIntent Stripe (AJAX) |
| `/payment/<order_id>/stripe/checkout/` | Page Stripe Elements |
| `/payment/stripe/success/` | Retour Stripe après paiement (marketplace + cours) |
| `/payment/<order_id>/plopplop/` | Initiation PlopPlop (redirect) |
| `/payment/plopplop/retour/` | Retour PlopPlop après paiement |
| `/academy/<slug>/pay/` | Choix du mode de paiement (cours payant) |
| `/academy/<slug>/pay/stripe/init/` | Création du PaymentIntent pour un cours (AJAX) |
| `/academy/<slug>/pay/stripe/` | Page Stripe Elements pour un cours |
| `/academy/<slug>/pay/plopplop/` | Initiation PlopPlop pour un cours |
| `/api/payments/stripe/webhook/` | Webhook Stripe (CSRF-exempt, re-vérifié) |
| `/api/payments/plopplop/webhook/` | Webhook PlopPlop (CSRF-exempt, re-vérifié) |

### Panel admin

| URL | Page |
|---|---|
| `/panel/` | Dashboard admin (stats, KPIs) |
| `/panel/listings/` | Toutes les annonces (recherche + pagination) |
| `/panel/listings/<id>/` | Revue / approbation annonce |
| `/panel/pickups/` | Tous les ramassages |
| `/panel/pickups/<id>/` | Détail + assignation collecteur |
| `/panel/users/` | Gestion utilisateurs |
| `/panel/users/<id>/` | Détail utilisateur |
| `/panel/auctions/` | Toutes les enchères (filtres, pagination) |
| `/panel/auctions/create/` | Créer une enchère (sélection listing, type, prix, durée) |
| `/panel/auctions/<id>/` | Détail enchère + historique offres + annuler/clôturer |
| `/panel/orders/` | Toutes les commandes (recherche + pagination) |
| `/panel/orders/<id>/` | Détail commande + notes internes |
| `/panel/blog/` | Gestion articles |
| `/panel/blog/create/` | Créer un article |
| `/panel/blog/<id>/edit/` | Éditer un article |
| `/panel/blog/categories/` | Catégories blog |
| `/panel/academy/` | Gestion cours (filtres: niveau, statut, prix) |
| `/panel/academy/create/` | Créer un cours (avec champ prix HTG) |
| `/panel/academy/<id>/` | Détail cours + liste leçons + inscriptions |
| `/panel/academy/<course_id>/lessons/create/` | Créer leçon + première vidéo |
| `/panel/academy/<course_id>/lessons/<id>/edit/` | Éditer leçon + CRUD vidéos |
| `/panel/academy/enrollments/` | Toutes les inscriptions |
| `/panel/academy/certificates/` | Tous les certificats + PDF |
| `/panel/newsletters/` | Abonnés newsletter |
| `/panel/contacts/` | Messages de contact |
| `/panel/config/` | Configuration du site (SiteConfiguration) |
| `/panel/sliders/` | Slides de la page d'accueil |

## Service de paiement (`apps/payments`)

### Modèle `Transaction`

```python
Transaction
├── order       (OneToOne → marketplace.Order, nullable)
├── enrollment  (OneToOne → academy.Enrollment, nullable)
├── transaction_number  # EC-YYYYMMDD-XXXXXXXX (auto-généré)
├── amount, currency    # HTG
├── status      # pending / completed / failed / cancelled / refunded
├── payment_method  # credit_card / moncash / natcash / kashpaw
├── external_transaction_id
├── meta_data   # JSON (stripe_client_secret, plopplop_url…)
└── completed_at
```

Une `Transaction` couvre soit une commande marketplace, soit une inscription de cours — jamais les deux.

### `process_successful_payment()` — fonction centrale idempotente

```
Transaction confirmée
  ├── Si transaction.order → Order.status = 'paid'
  │     → email confirmation acheteur + email vendeur
  │     → notify_order_paid (push acheteur+vendeur + impact record)
  └── Si transaction.enrollment → Enrollment.payment_status = 'paid'
        → email confirmation inscription cours
```

### Flux Stripe

```
Checkout page (choix mode)
  → AJAX POST stripe/init/ → PaymentIntent créé, client_secret stocké
  → Stripe Elements page → stripe.confirmPayment()
  → Redirect vers /payment/stripe/success/?payment_intent=pi_xxx
  → StripeSuccessView re-vérifie côté Stripe → process_successful_payment()
  (+ webhook payment_intent.succeeded en parallèle, idempotent)
```

### Flux PlopPlop (mobile money haïtien)

```
Checkout page
  → POST plopplop/ → PlopPlopService.create_payment() → redirect vers URL PlopPlop
  → Retour sur /payment/plopplop/retour/?reference_id=EC-xxx
  → PlopPlopReturnView re-vérifie côté PlopPlop → process_successful_payment()
  (+ webhook PlopPlop en parallèle, idempotent)
```

### Services

| Service | Rôle |
|---|---|
| `StripeService` | `create_payment_intent`, `retrieve_payment_intent`, `construct_webhook_event` |
| `PlopPlopService` | `create_payment`, `verify_payment` (passerelle `plopplop.solutionip.app`) |
| `ExchangeService` | Taux HTG via `open.er-api.com`, cache Django 1h |

## Marketplace — enchères sécurisées

### Sécurité API

- `select_for_update()` + `transaction.atomic()` sur `PlaceBidView` et `BuyNowView` → zéro race condition
- `auction_type` enforced : `auction` / `buy_now` / `both`
- `reserve_price` enforced dans `close_expired_auctions`
- `CreateAuctionSerializer` : validation dates + `buy_now_price` requis si type `buy_now`/`both`

### Flux d'achat

```
BuyNow / Enchère gagnante
  → Order créé (status: pending_payment)
  → Redirect vers /payment/<order_id>/
  → Paiement Stripe ou PlopPlop
  → Order.status = 'paid'
  → Celery: notify_order_paid → push buyer+seller + email seller + ImpactRecord
```

### Gestion admin enchères

- Liste avec filtres (statut, type) et pagination
- Détail : infos financières, historique offres (rang, avatar, badge "En tête"), profil vendeur, commande liée
- Actions : annuler ou clôturer manuellement une enchère active
- Création manuelle via `/panel/auctions/create/` : sélection listing approuvé, type, prix de départ/achat immédiat/réserve, durée prédéfinie ou dates personnalisées

### Approbation → création automatique d'enchère

Lorsqu'un admin approuve un listing, le formulaire d'approbation expose :
- **Type d'enchère** : Enchère / Achat immédiat / Les deux
- **Prix de départ** (pré-rempli avec la valeur estimée par l'IA)
- **Prix achat immédiat** (optionnel)
- **Durée** : 3 / 7 / 14 / 30 jours

L'`Auction` est créée automatiquement au statut `active` dès l'approbation. Le vendeur reçoit une notification push + email.

## Academy — e-learning (gratuit + payant)

### Modèles

- `Course` : titre, description, niveau, thumbnail, `price` (HTG, 0 = gratuit), is_published, durée auto-calculée
- `Lesson` : titre, contenu, PDF (extract ou embed), ordre, durée auto-calculée (somme vidéos)
- `LessonVideo` : fichier MP4/WebM **ou** URL externe (YouTube, Vimeo), embed automatique
- `Enrollment` : progression, `progress_percent`, `is_completed`, `payment_status` (free/pending/paid)
- `Certificate` : délivré automatiquement à 100% de progression, PDF téléchargeable

### Cours payants

```
Course.price > 0 → cours payant
  → Bouton "Payer et s'inscrire" sur la fiche cours
  → Enrollment créé (payment_status = pending)
  → Redirect vers /academy/<slug>/pay/ (même UI que marketplace)
  → Paiement Stripe ou PlopPlop
  → Enrollment.payment_status = 'paid'
  → Email confirmation inscription
  → Accès débloqué à toutes les leçons

LessonDetailView bloque si payment_status != 'paid' pour un cours payant
```

### Flux completion (cours gratuit ou payant)

```
User marque la dernière leçon comme terminée
  → Enrollment.update_progress()
  → 100% → Certificate créé
  → Celery: email certificat au user + notification admins
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
| POST | `/auctions/<id>/bid/` | Placer une enchère (atomic, select_for_update) |
| POST | `/auctions/<id>/buy-now/` | Achat immédiat (atomic, select_for_update) |
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
| Clôture des enchères expirées + reserve price check + notification vendeur | Toutes les 5 minutes |
| Annulation des ramassages non assignés après 72h | Toutes les heures |
| Rapport hebdomadaire admin | Lundi 8h (heure Haïti) |

### Tâches déclenchées par événement

| Tâche | Déclencheur |
|---|---|
| `notify_listing_approved` | Admin approuve une annonce → email + push vendeur |
| `notify_listing_rejected` | Admin rejette une annonce → email + push vendeur |
| `notify_new_bid` | Nouvelle enchère placée → push vendeur |
| `notify_auction_closed` | Enchère clôturée → push gagnant + email + order |
| `notify_order_created` | Commande créée (BuyNow) → push acheteur |
| `notify_order_paid` | Paiement confirmé → push buyer+seller + email seller + ImpactRecord |
| `notify_collector_assigned` | Collecteur assigné → push user + push collecteur + email |
| `notify_pickup_status_update` | Statut ramassage changé → push user |
| `notify_course_completed` | Cours terminé → email certificat + alerte admins |
| `notify_contact_message` | Formulaire de contact → alerte admins |
| `notify_newsletter_signup` | Inscription newsletter → double opt-in |
| `notify_admin_new_pickup` | Nouvelle demande ramassage → push admins |
| `create_impact_record` | Paiement confirmé (seulement) → calcul CO2 + leaderboard |

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
| `STRIPE_PUBLIC_KEY` | Oui | Clé publique Stripe |
| `STRIPE_SECRET_KEY` | Oui | Clé secrète Stripe |
| `STRIPE_WEBHOOK_SECRET` | Oui | Secret de signature webhook Stripe |
| `PLOPPLOP_CLIENT_ID` | Oui | Client ID passerelle PlopPlop |
| `PLOPPLOP_RETURN_URL` | Non | URL de retour PlopPlop (défaut : `http://localhost:8000/payment/plopplop/retour/`) |
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
├── WasteListing (photo, analyse IA, statut)
│     └── Auction (type: auction/buy_now/both, reserve_price)
│           ├── Bid (select_for_update, is_winning)
│           └── Order (pending_payment → paid → completed)
│                 └── Transaction (EC-YYYYMMDD-XXXXXXXX, Stripe ou PlopPlop)
│                       └── ImpactRecord (CO2, déclenché après paiement réel)
├── PickupRequest (statut, historique JSON) → ImpactRecord
├── Enrollment (payment_status: free/pending/paid) → LessonProgress → Certificate (PDF)
│     └── Transaction (même modèle que marketplace, enrollment nullable)
└── UserImpactSummary (CO2 total, rang communauté)

Course (price HTG, is_free property) → Lesson → LessonVideo (fichier ou URL YouTube/Vimeo)
SiteConfiguration (singleton: slider, liens app, contact, maintenance_mode)
```

## Flux principal

```
Photo mobile / web
  → POST /api/waste/analyze/ (analyse IA Claude Vision)
  → POST /api/waste/listings/ (draft)
  → Admin approuve → statut: approved + Auction créée automatiquement (active)
  → Enchère gagnante / achat immédiat → Order (pending_payment)
  → /payment/<order_id>/ → Stripe ou PlopPlop
  → process_successful_payment() → Order.status = paid
  → Celery: ImpactRecord (CO2 calculé) + notifications buyer + seller
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
- `select_for_update()` + `transaction.atomic()` sur toutes les opérations d'enchère et d'achat
- Webhooks paiement : CSRF-exempt + re-vérification serveur (jamais de confiance aveugle au payload)
- Noms d'URL distincts entre API (`apps/*/urls.py`) et web (`web/urls.py`)

## Licence

Projet propriétaire — EcoCycle Haiti © 2026. Créé par Eliézer Léonce, Valcin Vaillant et Lafleur.
