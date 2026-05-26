# EcoCycle Haiti — Spécification Application Mobile Flutter

> Document de référence pour le développement de l'application mobile Flutter.
> Reflète fidèlement le backend Django + DRF existant.
> **Base URL prod :** `https://ecoc.up.railway.app`

---

## Table des matières

1. [Architecture & Auth](#1-architecture--auth)
2. [Rôles utilisateurs](#2-rôles-utilisateurs)
3. [Endpoints API — Référence complète](#3-endpoints-api--référence-complète)
   - 3.1 [Authentification](#31-authentification--apiauth)
   - 3.2 [Déchets (Waste)](#32-déchets-waste--apiwaste)
   - 3.3 [Ramassages (Collections)](#33-ramassages-collections--apicollections)
   - 3.4 [Marketplace](#34-marketplace--apimarketplace)
   - 3.5 [Academy](#35-academy--apiacademy)
   - 3.6 [Notifications](#36-notifications--apinotifications)
   - 3.7 [Impact](#37-impact--apiimpact)
   - 3.8 [Blog](#38-blog--apiblog)
   - 3.9 [Contact & Newsletter](#39-contact--newsletter--apicontact-apinewsletter)
   - 3.10 [Documentation API](#310-documentation-api)
   - 3.11 [Admin global](#311-admin-global--apiadmin)
4. [Fonctionnalités par rôle](#4-fonctionnalités-par-rôle)
   - 4.1 [Utilisateur standard](#41-utilisateur-standard)
   - 4.2 [Collecteur](#42-collecteur)
   - 4.3 [Administrateur](#43-administrateur)
5. [Notifications Push (FCM)](#5-notifications-push-fcm)
6. [Écrans — Inventaire complet](#6-écrans--inventaire-complet)
7. [Modèles de données clés](#7-modèles-de-données-clés)
8. [Notes d'implémentation Flutter](#8-notes-dimplémentation-flutter)

---

## 1. Architecture & Auth

### Stack technique recommandé Flutter

| Besoin | Package recommandé |
|--------|-------------------|
| HTTP | `dio` + interceptors |
| Auth tokens | `flutter_secure_storage` |
| State | `riverpod` ou `bloc` |
| Navigation | `go_router` |
| Push FCM | `firebase_messaging` |
| Images | `cached_network_image` |
| Vidéo | `youtube_player_flutter`, `video_player` |
| Cartes | `flutter_map` + `latlong2` |
| Paiements | Stripe SDK (`flutter_stripe`) |
| PDF | `flutter_pdfview` |
| Markdown | `flutter_markdown` |

### Authentification JWT

- **Access token** : validité 1 heure — à inclure dans chaque requête protégée
- **Refresh token** : validité 30 jours — stocké en secure storage
- **Header** : `Authorization: Bearer <access_token>`
- **Refresh** : `POST /api/auth/token/refresh/` avec `{ "refresh": "..." }`

```
Flux de login :
1. POST /api/auth/login/  → { access, refresh, user }
2. Stocker access + refresh en secure storage
3. Intercepteur Dio : si 401 → appel refresh → retry
4. Logout : POST /api/auth/logout/ avec le refresh token (blacklist)
```

---

## 2. Rôles utilisateurs

| Rôle | Valeur API | Accès |
|------|-----------|-------|
| Utilisateur standard | `user` | Listings, Ramassages, Marketplace, Academy |
| Ramasseur | `collector` | + Gestion des ramassages assignés |
| Administrateur | `admin` | + Panel admin complet, toutes les ressources |

Le rôle est retourné dans `user.role` lors du login/profile. L'app doit afficher des menus et écrans différents selon le rôle.

---

## 3. Endpoints API — Référence complète

### 3.1 Authentification — `/api/auth/`

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| POST | `/api/auth/register/` | Non | Créer un compte |
| POST | `/api/auth/login/` | Non | Connexion → tokens + profil |
| POST | `/api/auth/logout/` | Oui | Blacklist le refresh token |
| POST | `/api/auth/token/refresh/` | Non | Renouveler l'access token |
| GET | `/api/auth/verify-email/<token>/` | Non | Vérifier email via lien |
| GET | `/api/auth/profile/` | Oui | Lire le profil |
| PUT/PATCH | `/api/auth/profile/` | Oui | Modifier le profil |
| POST | `/api/auth/change-password/` | Oui | Changer le mot de passe |
| POST | `/api/auth/fcm-token/` | Oui | Enregistrer/mettre à jour le token FCM |
| POST | `/api/auth/reset-password/` | Non | Demande de réinitialisation (envoi email) |
| POST | `/api/auth/reset-password/confirm/` | Non | Confirmer avec token + nouveau mdp |

**Register — Body :**
```json
{
  "email": "user@example.com",
  "first_name": "Jean",
  "last_name": "Pierre",
  "phone": "+50912345678",
  "password": "motdepasse123",
  "password_confirm": "motdepasse123"
}
```

**Login — Body :**
```json
{ "email": "user@example.com", "password": "motdepasse123" }
```

**Login — Réponse :**
```json
{
  "user": {
    "id": "uuid",
    "email": "...",
    "first_name": "Jean",
    "last_name": "Pierre",
    "full_name": "Jean Pierre",
    "phone": "...",
    "role": "user",
    "avatar": "https://....",
    "bio": "...",
    "address": "...",
    "city": "Port-au-Prince",
    "is_email_verified": true,
    "total_listings": 3,
    "total_kg_recycled": 12.5,
    "created_at": "..."
  },
  "tokens": {
    "access": "eyJ...",
    "refresh": "eyJ..."
  }
}
```

---

### 3.2 Déchets (Waste) — `/api/waste/`

| Méthode | Endpoint | Auth | Rôle | Description |
|---------|----------|------|------|-------------|
| GET | `/api/waste/categories/` | Non | Tous | Liste des catégories actives |
| GET | `/api/waste/listings/` | Oui | User | Mes listings |
| POST | `/api/waste/listings/` | Oui | User | Créer un listing (multipart) |
| GET | `/api/waste/listings/<id>/` | Oui | Owner/Admin | Détail d'un listing |
| PUT/PATCH | `/api/waste/listings/<id>/` | Oui | Owner/Admin | Modifier un listing |
| DELETE | `/api/waste/listings/<id>/` | Oui | Owner/Admin | Supprimer un listing |
| POST | `/api/waste/analyze/` | Oui | User | Analyse IA avant soumission |
| GET | `/api/waste/admin/listings/` | Oui | Admin | Tous les listings |
| POST | `/api/waste/admin/listings/<id>/review/` | Oui | Admin | Approuver/rejeter |

**Créer un listing — multipart/form-data :**
```
title          : string
description    : string
category       : UUID (id de catégorie)
quantity_kg    : decimal
photo          : image file
pickup_address : string
city           : string
latitude       : decimal (optionnel)
longitude      : decimal (optionnel)
```

**Après soumission :** l'IA Claude Vision analyse automatiquement la photo en arrière-plan. Le champ `ai_analysis` est peuplé async.

**Analyse IA — Body (preview avant soumission) :**
```json
{ "image_base64": "data:image/jpeg;base64,/9j/..." }
```
ou
```json
{ "image_url": "https://..." }
```

**Réponse analyse IA :**
```json
{
  "analysis": {
    "category_slug": "plastique",
    "estimated_value_htg": 450,
    "description": "Bouteilles PET en bon état...",
    "recyclability_score": 8
  }
}
```

**Statuts listing :**
| Valeur | Signification |
|--------|--------------|
| `pending_review` | En attente d'approbation admin |
| `approved` | Approuvé, visible sur la marketplace |
| `rejected` | Rejeté (raison dans `rejection_reason`) |
| `sold` | Vendu via enchère |

**Admin review — Body :**
```json
{ "action": "approve" }
// ou
{ "action": "reject", "rejection_reason": "Photo non conforme." }
```

---

### 3.3 Ramassages (Collections) — `/api/collections/`

| Méthode | Endpoint | Auth | Rôle | Description |
|---------|----------|------|------|-------------|
| GET | `/api/collections/` | Oui | User | Mes demandes de ramassage |
| POST | `/api/collections/` | Oui | User | Créer une demande |
| GET | `/api/collections/<id>/` | Oui | Owner/Admin | Détail d'un ramassage |
| GET | `/api/collections/admin/` | Oui | Admin | Tous les ramassages |
| POST | `/api/collections/<id>/assign/` | Oui | Admin | Assigner un collecteur |
| GET | `/api/collections/collector/` | Oui | Collector | Mes ramassages assignés |
| POST | `/api/collections/<id>/status/` | Oui | Collector | Mettre à jour le statut |

**Créer un ramassage — Body :**
```json
{
  "listing": "uuid-du-listing",
  "address": "Rue Capois #12",
  "city": "Port-au-Prince",
  "latitude": 18.543,
  "longitude": -72.338,
  "preferred_date": "2026-06-01",
  "preferred_slot": "morning",
  "special_instructions": "Sonner deux fois"
}
```
> `listing` est optionnel (ramassage sans listing lié possible)

**Créneaux horaires :**
| Valeur | Label |
|--------|-------|
| `morning` | Matin (8h-12h) |
| `afternoon` | Après-midi (12h-17h) |
| `evening` | Soir (17h-20h) |

**Statuts ramassage :**
| Valeur | Label | Acteur |
|--------|-------|--------|
| `requested` | Demandé | (initial) |
| `assigned` | Assigné | Admin |
| `in_transit` | En transit | Collecteur |
| `arrived` | Arrivé | Collecteur |
| `completed` | Complété | Collecteur |
| `failed` | Échoué | Collecteur |
| `cancelled` | Annulé | Admin/User |

**Assigner un collecteur — Body :**
```json
{ "collector_id": "uuid-du-collecteur" }
```

**Mettre à jour le statut — Body :**
```json
{
  "status": "completed",
  "note": "Collecte effectuée sans problème",
  "actual_weight_kg": 15.5
}
```

---

### 3.4 Marketplace — `/api/marketplace/`

| Méthode | Endpoint | Auth | Rôle | Description |
|---------|----------|------|------|-------------|
| GET | `/api/marketplace/auctions/` | Non | Tous | Enchères actives |
| GET | `/api/marketplace/auctions/<id>/` | Non | Tous | Détail enchère |
| POST | `/api/marketplace/auctions/create/` | Oui | User | Créer une enchère |
| POST | `/api/marketplace/auctions/<id>/bid/` | Oui | User | Placer une offre |
| POST | `/api/marketplace/auctions/<id>/buy-now/` | Oui | User | Achat immédiat |
| GET | `/api/marketplace/orders/my/` | Oui | User | Mes commandes (acheteur) |
| GET | `/api/marketplace/orders/sales/` | Oui | User | Mes ventes (vendeur) |
| GET | `/api/marketplace/admin/orders/` | Oui | Admin | Toutes les commandes |

**Filtres disponibles sur `/api/marketplace/auctions/` :**
- `status=active`
- `auction_type=auction|buy_now|both`
- `listing__category=<uuid>`
- `search=<terme>`
- `ordering=created_at|-created_at|ends_at|current_price|total_bids`

**Types d'enchère :**
| Valeur | Signification |
|--------|--------------|
| `auction` | Enchère classique uniquement |
| `buy_now` | Achat immédiat uniquement |
| `both` | Enchère + achat immédiat |

**Créer une enchère — Body :**
```json
{
  "listing_id": "uuid-du-listing-approuve",
  "auction_type": "both",
  "starting_price": 500,
  "buy_now_price": 2000,
  "reserve_price": 800,
  "starts_at": "2026-06-01T08:00:00Z",
  "ends_at": "2026-06-08T20:00:00Z"
}
```

**Placer une offre — Body :**
```json
{ "amount": 750 }
```
> Minimum = `current_price + 10 HTG`

**Réponse enchère — champs clés :**
```json
{
  "id": "uuid",
  "listing": { "...listing complet..." },
  "seller_name": "Marie Louis",
  "auction_type": "both",
  "starting_price": "500.00",
  "buy_now_price": "2000.00",
  "current_price": "750.00",
  "status": "active",
  "ends_at": "2026-06-08T20:00:00Z",
  "time_remaining": 604800,
  "total_bids": 3,
  "latest_bids": [...],
  "user_bid": { "amount": "650.00", ... }
}
```

**Statuts commande :**
| Valeur | Signification |
|--------|--------------|
| `pending_payment` | En attente de paiement |
| `paid` | Payé |
| `completed` | Livré/complété |
| `cancelled` | Annulé |

---

### 3.5 Academy — `/api/academy/`

#### Endpoints utilisateur

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/api/academy/courses/` | Non | Liste des cours publiés |
| GET | `/api/academy/courses/<slug>/` | Non | Détail cours + leçons + vidéos |
| POST | `/api/academy/courses/<slug>/enroll/` | Oui | S'inscrire au cours |
| POST | `/api/academy/lessons/<id>/complete/` | Oui | Marquer leçon terminée |
| GET | `/api/academy/my-enrollments/` | Oui | Mes cours en cours |
| GET | `/api/academy/my-certificates/` | Oui | Mes certificats |

**Filtres `/api/academy/courses/` :**
- `level=beginner|intermediate|advanced`
- `is_free=true|false`
- `search=<terme>`

**Réponse cours détaillé :**
```json
{
  "id": "uuid",
  "title": "Recyclage du plastique",
  "slug": "recyclage-du-plastique",
  "description": "...",
  "thumbnail": "https://...",
  "level": "beginner",
  "level_display": "Débutant",
  "duration_minutes": 120,
  "is_free": true,
  "lesson_count": 8,
  "enrollment_count": 145,
  "lessons": [
    {
      "id": "uuid",
      "title": "Introduction",
      "content": "Markdown content...",
      "pdf_display_mode": "extract",
      "pdf_allow_download": false,
      "order": 1,
      "duration_minutes": 15,
      "videos": [
        {
          "id": "uuid",
          "title": "Intro vidéo",
          "video_file": null,
          "video_url": "https://youtu.be/dQw4w9WgXcQ",
          "embed_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
          "platform": "youtube",
          "allow_download": false,
          "duration_minutes": 12,
          "order": 1
        }
      ]
    }
  ]
}
```

**Valeurs `platform` :**
| Valeur | Signification |
|--------|--------------|
| `youtube` | Vidéo YouTube |
| `vimeo` | Vidéo Vimeo |
| `tiktok` | Vidéo TikTok |
| `instagram` | Reel Instagram |
| `direct` | Fichier MP4/WebM uploadé |
| `unknown` | URL non reconnue |

**Valeurs `pdf_display_mode` :**
| Valeur | Signification |
|--------|--------------|
| `extract` | Texte extrait du PDF, rendu en Markdown |
| `viewer` | Visionneuse PDF intégrée (`flutter_pdfview`) |

**Réponse enrollment :**
```json
{
  "id": "uuid",
  "course": "uuid",
  "course_title": "Recyclage du plastique",
  "course_slug": "recyclage-du-plastique",
  "progress_percent": 62,
  "is_completed": false,
  "completed_lesson_ids": ["uuid1", "uuid2"],
  "payment_status": "free",
  "enrolled_at": "2026-05-01T...",
  "completed_at": null
}
```

#### Paiement d'un cours — Stripe

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| POST | `/api/academy/courses/<slug>/pay/stripe/init/` | Oui | Initialiser un PaymentIntent Stripe |
| POST | `/api/academy/courses/<slug>/pay/stripe/confirm/` | Oui | Confirmer après paiement Flutter |

**Stripe init — Réponse :**
```json
{
  "client_secret": "pi_xxx_secret_yyy",
  "transaction_number": "TXN-XXXXXX"
}
```

**Stripe confirm — Body :**
```json
{ "payment_intent_id": "pi_xxx" }
```

**Stripe confirm — Réponse :** objet `Enrollment` complet (voir ci-dessus).

**Flux Flutter Stripe :**
```dart
// 1. Init
final res = await api.post('/api/academy/courses/$slug/pay/stripe/init/');
final clientSecret = res['client_secret'];

// 2. Présenter la feuille de paiement
await Stripe.instance.initPaymentSheet(
  paymentSheetParameters: SetupPaymentSheetParameters(
    paymentIntentClientSecret: clientSecret,
    merchantDisplayName: 'EcoCycle Haiti',
  ),
);
await Stripe.instance.presentPaymentSheet();

// 3. Confirmer côté backend
final pi = await Stripe.instance.retrievePaymentIntent(clientSecret);
await api.post('/api/academy/courses/$slug/pay/stripe/confirm/', {
  'payment_intent_id': pi.id,
});
```

#### Paiement d'un cours — PlopPlop

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| POST | `/api/academy/courses/<slug>/pay/plopplop/` | Oui | Créer le paiement PlopPlop |
| GET | `/api/academy/courses/<slug>/pay/plopplop/retour/?reference_id=...` | Non | Vérifier après retour WebView |

**PlopPlop init — Body :**
```json
{ "method": "moncash" }
```
> Valeurs `method` : `moncash` | `natcash` | `kashpaw` | `all`

**PlopPlop init — Réponse :**
```json
{
  "redirect_url": "https://plopplop.com/pay/...",
  "transaction_number": "TXN-XXXXXX"
}
```

**PlopPlop retour — Réponse (si payé) :**
```json
{
  "status": "paid",
  "enrollment": { "...enrollment complet..." }
}
```
> `status` peut être `"paid"` ou `"already_paid"`. En cas d'échec : HTTP 402.

**Flux Flutter PlopPlop :**
```dart
// 1. Init
final res = await api.post('/api/academy/courses/$slug/pay/plopplop/', {'method': 'moncash'});
final redirectUrl = res['redirect_url'];
final txnNumber   = res['transaction_number'];

// 2. Ouvrir WebView
// Écouter la navigation vers l'URL de retour (contient ?reference_id=...)
// 3. Vérifier
final verify = await api.get(
  '/api/academy/courses/$slug/pay/plopplop/retour/?reference_id=$txnNumber',
);
```

#### Endpoints admin Academy

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/api/academy/admin/courses/` | Admin | Liste tous les cours |
| POST | `/api/academy/admin/courses/` | Admin | Créer un cours (multipart) |
| GET | `/api/academy/admin/courses/<slug>/` | Admin | Détail d'un cours |
| PUT/PATCH | `/api/academy/admin/courses/<slug>/` | Admin | Modifier un cours |
| DELETE | `/api/academy/admin/courses/<slug>/` | Admin | Supprimer un cours |
| GET | `/api/academy/admin/lessons/` | Admin | Liste toutes les leçons |
| POST | `/api/academy/admin/lessons/` | Admin | Créer une leçon (multipart) |
| GET | `/api/academy/admin/lessons/<id>/` | Admin | Détail d'une leçon |
| PUT/PATCH | `/api/academy/admin/lessons/<id>/` | Admin | Modifier une leçon |
| DELETE | `/api/academy/admin/lessons/<id>/` | Admin | Supprimer une leçon |
| POST | `/api/academy/admin/lessons/<id>/videos/` | Admin | Ajouter une vidéo à une leçon |
| DELETE | `/api/academy/admin/videos/<id>/` | Admin | Supprimer une vidéo |

**Filtres `/api/academy/admin/courses/` :** `level`, `is_published`, `search`, `ordering`

**Filtres `/api/academy/admin/lessons/` :** `course=<uuid>`, `ordering=order`

**Créer un cours — multipart/form-data :**
```
title            : string
description      : string
level            : beginner | intermediate | advanced
is_free          : boolean
price            : decimal (si is_free=false)
thumbnail        : image file (optionnel)
is_published     : boolean
```

**Créer une leçon — multipart/form-data :**
```
course           : UUID
title            : string
content          : string (Markdown)
order            : integer
pdf_file         : file (optionnel)
pdf_display_mode : extract | viewer
pdf_allow_download : boolean
```
> Si `pdf_display_mode=extract`, le backend calcule automatiquement `pdf_reading_minutes`.

**Ajouter une vidéo — Body (JSON ou multipart) :**
```json
{
  "title": "Introduction",
  "video_url": "https://youtu.be/dQw4w9WgXcQ",
  "duration_minutes": 0,
  "allow_download": false,
  "order": 1
}
```
> Si `video_url` est une URL YouTube et `duration_minutes=0`, le backend récupère automatiquement la durée via l'API YouTube Data v3.
> Pour uploader un fichier : utiliser `multipart/form-data` avec champ `video_file`.

---

### 3.6 Notifications — `/api/notifications/`

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/api/notifications/` | Oui | Toutes mes notifications |
| GET | `/api/notifications/unread-count/` | Oui | Nombre de non lues |
| POST | `/api/notifications/<id>/read/` | Oui | Marquer une notif comme lue |
| POST | `/api/notifications/read-all/` | Oui | Tout marquer comme lu |

**Réponse notification :**
```json
{
  "id": "uuid",
  "notification_type": "listing_approved",
  "type_display": "Listing approuvé",
  "title": "Listing approuvé",
  "message": "Votre listing \"Bouteilles PET\" est maintenant en ligne.",
  "data": { "listing_id": "uuid" },
  "is_read": false,
  "created_at": "2026-05-20T10:30:00Z"
}
```

**Types de notifications (`notification_type`) :**
| Type | Description |
|------|-------------|
| `listing_approved` | Listing approuvé par un admin |
| `listing_rejected` | Listing rejeté |
| `new_bid` | Quelqu'un a enchéri sur votre listing |
| `auction_won` | Enchère remportée |
| `auction_lost` | Enchère perdue (quand fermée) |
| `outbid` | Vous avez été surenchéri |
| `auction_closed` | Enchère fermée sans acheteur |
| `order_created` | Commande créée |
| `order_paid` | Paiement confirmé |
| `pickup_assigned` | Ramassage assigné |
| `pickup_status` | Mise à jour statut ramassage |
| `pickup_completed` | Ramassage complété |
| `new_listing_admin` | Nouveau listing (admin) |
| `system` | Message système |

---

### 3.7 Impact — `/api/impact/`

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/api/impact/dashboard/` | Oui | Mon tableau de bord impact |
| GET | `/api/impact/leaderboard/` | Oui | Classement top 20 recycleurs |
| GET | `/api/impact/stats/` | Non | Statistiques globales |

**Dashboard impact :**
```json
{
  "summary": {
    "user": "uuid",
    "user_name": "Jean Pierre",
    "total_kg_recycled": 47.5,
    "total_co2_saved_kg": 23.75,
    "total_economic_value_htg": 12500,
    "total_transactions": 8,
    "community_rank": 12,
    "updated_at": "..."
  },
  "recent_records": [
    {
      "id": "uuid",
      "category_slug": "plastique",
      "kg_recycled": 5.0,
      "co2_saved_kg": 2.5,
      "economic_value_htg": 1500,
      "created_at": "..."
    }
  ]
}
```

**Stats globales (page d'accueil) :**
```json
{
  "total_kg_recycled": 1234.5,
  "total_co2_saved_kg": 617.25,
  "total_users": 487,
  "total_orders": 123,
  "total_pickups": 289
}
```

---

### 3.8 Blog — `/api/blog/`

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/api/blog/posts/` | Non | Liste des articles publiés |
| GET | `/api/blog/posts/<slug>/` | Non | Détail d'un article |

**Filtres `/api/blog/posts/` :**
- `category=<id>`
- `search=<terme>`
- `ordering=published_at|views|read_time_minutes`

---

### 3.9 Contact & Newsletter — `/api/contact/`, `/api/newsletter/`

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| POST | `/api/contact/` | Non | Envoyer un message de contact |
| POST | `/api/newsletter/subscribe/` | Non | S'abonner à la newsletter |
| GET | `/api/newsletter/confirm/<token>/` | Non | Confirmer l'abonnement |

**Contact — Body :**
```json
{
  "first_name": "Jean",
  "last_name": "Pierre",
  "email": "jp@example.com",
  "subject": "Question sur le recyclage",
  "message": "Bonjour..."
}
```

---

### 3.10 Documentation API

| URL | Description |
|-----|-------------|
| `/api/docs/` | Swagger UI interactif |
| `/api/redoc/` | ReDoc |
| `/api/schema/` | OpenAPI JSON/YAML |
| `/health/` | Healthcheck Railway |

---

### 3.11 Admin global — `/api/admin/`

> Tous les endpoints de cette section sont réservés au rôle `admin` (permission `IsAdmin`).

#### Stats dashboard

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/api/admin/stats/` | Admin | Statistiques globales temps réel |

**Réponse :**
```json
{
  "listings_pending": 4,
  "pickups_active": 7,
  "auctions_active": 12,
  "marketplace_revenue_htg": 45000.0,
  "academy_enrollments": 289,
  "new_users_today": 3,
  "total_users": 512
}
```

| Champ | Signification |
|-------|--------------|
| `listings_pending` | Listings en attente d'approbation (`pending_review`) |
| `pickups_active` | Ramassages en cours (`assigned` + `in_transit` + `arrived`) |
| `auctions_active` | Enchères actives |
| `marketplace_revenue_htg` | Total des commandes payées (HTG) |
| `academy_enrollments` | Nombre total d'inscriptions Academy |
| `new_users_today` | Nouveaux inscrits aujourd'hui |
| `total_users` | Utilisateurs actifs |

#### Gestion des utilisateurs

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/api/admin/users/` | Admin | Liste tous les utilisateurs |
| GET | `/api/admin/users/<id>/` | Admin | Détail d'un utilisateur |
| PATCH | `/api/admin/users/<id>/` | Admin | Modifier rôle, statut, infos |

**Filtres `/api/admin/users/` :**
- `role=user|collector|admin`
- `is_active=true|false`
- `is_email_verified=true|false`
- `search=<email|prénom|nom|ville>`
- `ordering=created_at|email|role`

**Réponse utilisateur :**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Jean Pierre",
  "first_name": "Jean",
  "last_name": "Pierre",
  "phone": "+50912345678",
  "role": "user",
  "is_active": true,
  "is_email_verified": true,
  "city": "Port-au-Prince",
  "avatar": "https://...",
  "created_at": "2026-05-01T..."
}
```

**PATCH `/api/admin/users/<id>/` — Champs modifiables :**
```json
{
  "role": "collector",
  "is_active": false,
  "first_name": "Jean",
  "last_name": "Pierre",
  "phone": "+50912345678",
  "city": "Cap-Haïtien"
}
```
> `role` accepte uniquement : `user` | `collector` | `admin`

#### Liste des collecteurs disponibles

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/api/admin/collectors/` | Admin | Collecteurs et admins actifs |

> Utilisé pour la liste de sélection lors de l'assignation d'un ramassage.
> Retourne uniquement les utilisateurs avec `role in (collector, admin)` et `is_active=true`.

**Filtres :** `search=<email|prénom|nom|ville>`, `ordering=first_name|city`

**Réponse :** même format que `/api/admin/users/`.

---

## 4. Fonctionnalités par rôle

### 4.1 Utilisateur standard

#### Authentification
- [x] Inscription (email, prénom, nom, téléphone, mot de passe)
- [x] Connexion / Déconnexion
- [x] Vérification email (lien reçu par email → confirmation dans l'app via deep link)
- [x] Réinitialisation mot de passe (email → token → nouveau mdp)
- [x] Modification du profil (avatar, bio, adresse, ville, téléphone)
- [x] Changement de mot de passe

#### Tableau de bord (Home)
- [x] Stats globales EcoCycle (kg recyclés, CO2 économisé, utilisateurs)
- [x] Mes stats personnelles (kg recyclés, rang communautaire)
- [x] Accès rapide : Soumettre un déchet, Mes ramassages, Marketplace, Academy
- [x] Notifications non lues (badge)

#### Gestion des déchets
- [x] Liste de mes listings (statut, date, catégorie)
- [x] Créer un listing : photo, titre, description, catégorie, quantité, adresse de ramassage
- [x] Analyse IA de la photo AVANT soumission (prévisualisation de la valeur estimée)
- [x] Voir le résultat de l'analyse IA sur un listing existant
- [x] Modifier un listing (si pas encore approuvé)
- [x] Supprimer un listing
- [x] Voir le statut d'approbation et la raison de rejet si rejeté

#### Demandes de ramassage
- [x] Créer une demande de ramassage (lier à un listing ou non)
  - Adresse + géolocalisation (carte)
  - Date souhaitée
  - Créneau : Matin / Après-midi / Soir
  - Instructions spéciales
- [x] Liste de mes demandes avec statut en temps réel
- [x] Détail d'une demande (historique des statuts, infos collecteur)
- [x] Notifications push : collecteur en route, ramassage complété

#### Marketplace — Enchères
- [x] Parcourir les enchères actives (liste + filtres)
  - Filtre par catégorie
  - Filtre par type (enchère / achat immédiat)
  - Recherche par titre
  - Tri par date, prix, nombre d'offres
- [x] Détail d'une enchère
  - Photo + description du déchet
  - Prix actuel, temps restant (countdown live)
  - Historique des 5 dernières offres
  - Ma dernière offre
- [x] Placer une offre (enchère classique)
  - Validation minimum = prix actuel + 10 HTG
  - Notification si surenchéri
- [x] Achat immédiat (buy now)
- [x] Créer une enchère sur un de mes listings approuvés
  - Type : enchère / achat immédiat / les deux
  - Prix de départ, prix immédiat, prix de réserve
  - Dates de début et fin
- [x] Mes commandes (acheteur) — liste + statut
- [x] Mes ventes (vendeur) — liste + statut

#### Paiement (après achat/enchère gagnée)
- [x] Sélection du mode de paiement : Stripe (carte) ou PlopPlop (MonCash, NatCash, Kashpaw)
- [x] Flux Stripe : WebView ou flutter_stripe
- [x] Flux PlopPlop : WebView → retour app → confirmation

#### Academy (e-learning)
- [x] Catalogue des cours (filtres niveau, gratuit/payant, recherche)
- [x] Détail cours : description, durée, nombre de leçons, niveau
- [x] S'inscrire à un cours gratuit
- [x] Payer un cours payant via Stripe (`/pay/stripe/init/` + `flutter_stripe`)
- [x] Payer un cours payant via PlopPlop (`/pay/plopplop/` + WebView)
- [x] Mes cours en cours : progression (barre de progression)
- [x] Leçon — contenu :
  - Texte Markdown rendu
  - Vidéos intégrées : YouTube, Vimeo (lecture native), TikTok/Instagram (WebView), MP4 direct
  - PDF : mode texte extrait ou visionneuse PDF
- [x] Marquer une leçon comme terminée
- [x] Avancer automatiquement à la leçon suivante
- [x] Certificat généré automatiquement à la complétion du cours
- [x] Mes certificats (liste + téléchargement PDF)
- [x] Notifications : rappel 48h si cours commencé non terminé
- [x] Notifications : nouvelle leçon dans un cours inscrit

#### Impact personnel
- [x] Tableau de bord impact : kg recyclés, CO2 économisé, valeur économique, rang
- [x] Historique des transactions de recyclage
- [x] Classement communautaire (top 20)

#### Notifications in-app
- [x] Liste de toutes les notifications
- [x] Badge compteur non lues
- [x] Marquer comme lue (individuelle / tout)
- [x] Navigation vers l'objet concerné en cliquant la notif

#### Blog
- [x] Liste des articles (recherche, filtre catégorie)
- [x] Lecture d'un article

#### Contact
- [x] Formulaire de contact

#### Newsletter
- [x] Inscription à la newsletter + confirmation email

---

### 4.2 Collecteur

> Accès à **tout** ce que fait un utilisateur standard, **plus** :

#### Tableau de bord collecteur
- [x] Mes ramassages assignés (avec carte de localisation)
- [x] Statistiques : total complétés, en cours, échoués
- [x] Accès rapide aux ramassages en attente d'action

#### Gestion des ramassages assignés
- [x] Liste des ramassages assignés / en transit / arrivé
- [x] Détail d'un ramassage :
  - Nom et contact du client
  - Adresse + carte
  - Créneau horaire
  - Instructions spéciales
  - Listing associé (photo, description des déchets)
  - Historique des statuts
- [x] Mettre à jour le statut dans le flux :
  1. `in_transit` — Je suis en route
  2. `arrived` — Je suis arrivé
  3. `completed` — Ramassage complété (saisir poids réel en kg, note optionnelle)
  4. `failed` — Échec avec raison
- [x] Notifications : nouveau ramassage assigné

---

### 4.3 Administrateur

> Accès à **tout** ce que fait un utilisateur standard + collecteur, **plus** :

#### Dashboard admin
- [x] Stats globales en temps réel via `GET /api/admin/stats/` :
  - Listings en attente d'approbation
  - Ramassages actifs
  - Enchères actives
  - Revenus marketplace (HTG)
  - Inscriptions Academy
  - Nouveaux utilisateurs aujourd'hui
  - Total utilisateurs actifs
- [x] Alertes : nouveaux listings, nouveaux utilisateurs

#### Gestion des listings
- [x] Liste tous les listings (tous statuts, tous utilisateurs)
  - Filtre : statut, catégorie, ville
  - Recherche : titre, email utilisateur
  - Tri : date, valeur estimée IA
- [x] Approuver un listing → déclenche création automatique d'une enchère
- [x] Rejeter un listing (avec raison obligatoire)
- [x] Voir l'analyse IA du listing

#### Gestion des ramassages
- [x] Liste tous les ramassages (tous statuts, tous utilisateurs)
  - Filtre : statut, ville, date
  - Recherche : email client, ville, adresse
- [x] Assigner un collecteur à un ramassage via `GET /api/admin/collectors/`
- [x] Notification push + email à réception d'une nouvelle demande de ramassage

#### Gestion de la marketplace
- [x] Liste toutes les commandes (tous les acheteurs/vendeurs)
  - Filtre : statut
  - Tri : date, montant
- [x] Créer une enchère manuellement
- [x] Voir les enchères actives et leur état

#### Gestion de l'Academy (CRUD complet via API REST)
- [x] Créer / modifier / supprimer un cours — `POST/PATCH/DELETE /api/academy/admin/courses/`
- [x] Publier / dépublier un cours — champ `is_published`
- [x] Créer / modifier / supprimer des leçons — `POST/PATCH/DELETE /api/academy/admin/lessons/`
- [x] Ajouter des vidéos (YouTube auto-durée, Vimeo, TikTok, Instagram, MP4/WebM uploadé) — `POST /api/academy/admin/lessons/<id>/videos/`
- [x] Supprimer une vidéo — `DELETE /api/academy/admin/videos/<id>/`
- [x] Ajouter un PDF (mode texte extrait ou visionneuse, extraction auto des pages)
- [x] Voir les inscriptions par cours
- [x] Voir les certificats émis

#### Gestion des utilisateurs (via API REST)
- [x] Liste tous les utilisateurs via `GET /api/admin/users/`
  - Filtres : rôle, statut actif, email vérifié
  - Recherche : email, prénom, nom, ville
- [x] Modifier le rôle d'un utilisateur (user → collector → admin) via `PATCH /api/admin/users/<id>/`
- [x] Activer / désactiver un compte via `PATCH /api/admin/users/<id>/` (`is_active`)

#### Notifications admin reçues
- [x] Push + email : nouveau listing soumis
- [x] Push + email : nouvel utilisateur inscrit
- [x] Push + email : paiement reçu (marketplace ou academy)
- [x] Push + email : ramassage échoué
- [x] Push + email : inscription cours payant

---

## 5. Notifications Push (FCM)

### Setup Firebase

1. Créer un projet Firebase Console
2. Ajouter l'app Flutter (iOS + Android)
3. Télécharger `google-services.json` (Android) et `GoogleService-Info.plist` (iOS)
4. Package Flutter : `firebase_messaging`

### Enregistrement du token

Après chaque login ET à chaque démarrage de l'app si l'utilisateur est connecté :

```dart
FirebaseMessaging.instance.getToken().then((token) {
  if (token != null) {
    api.post('/api/auth/fcm-token/', { 'fcm_token': token });
  }
});
// Écouter le renouvellement du token
FirebaseMessaging.instance.onTokenRefresh.listen((token) {
  api.post('/api/auth/fcm-token/', { 'fcm_token': token });
});
```

### Payload des notifications

Chaque notification push contient un champ `data` avec le contexte pour la navigation :

```json
// Listing approuvé
{ "type": "listing_approved", "listing_id": "uuid" }

// Surenchéri
{ "type": "outbid", "auction_id": "uuid" }

// Enchère gagnée
{ "type": "auction_won", "auction_id": "uuid" }

// Enchère perdue (fin d'enchère)
{ "type": "auction_lost", "auction_id": "uuid" }

// Statut ramassage mis à jour
{ "type": "pickup_status", "pickup_id": "uuid", "status": "in_transit" }

// Cours complété → certificat dispo
{ "type": "course_completed", "course_id": "uuid", "cert_id": "uuid" }

// Rappel leçon non terminée (48-72h après dernière activité)
{ "type": "lesson_reminder", "course_slug": "recyclage-du-plastique" }

// Nouvelle leçon dans un cours inscrit
{ "type": "new_lesson", "course_slug": "...", "lesson_id": "uuid" }

// Admin : nouveau listing
{ "type": "admin_new_listing", "listing_id": "uuid" }

// Admin : nouvel utilisateur
{ "type": "admin_new_user", "user_id": "uuid" }

// Admin : paiement reçu
{ "type": "admin_payment_received", "transaction_id": "uuid" }

// Admin : ramassage échoué
{ "type": "admin_pickup_failed", "pickup_id": "uuid" }

// Admin : inscription cours payant
{ "type": "admin_paid_enrollment", "enrollment_id": "uuid" }
```

### Navigation depuis notification (deep link)

| `type` | Écran cible |
|--------|-------------|
| `listing_approved` / `listing_rejected` | Détail listing |
| `new_bid` | Détail enchère |
| `outbid` | Détail enchère |
| `auction_won` / `auction_lost` | Détail enchère |
| `order_created` / `order_paid` | Détail commande |
| `pickup_assigned` / `pickup_status` | Détail ramassage |
| `course_completed` | Mes certificats |
| `lesson_reminder` | Cours → continuer |
| `new_lesson` | Cours → liste leçons |
| `admin_*` | Écran admin correspondant |

---

## 6. Écrans — Inventaire complet

### Navigation principale (Bottom Nav Bar)

```
[ Accueil ]  [ Marketplace ]  [ + Soumettre ]  [ Academy ]  [ Profil ]
```

---

### Écrans publics (non authentifié)

| Écran | Description |
|-------|-------------|
| `SplashScreen` | Logo + animation, redirige selon auth state |
| `OnboardingScreen` | Présentation de l'app (3-4 slides) |
| `LoginScreen` | Email + mot de passe, lien inscription, lien mot de passe oublié |
| `RegisterScreen` | Formulaire complet inscription |
| `ForgotPasswordScreen` | Saisie email → envoi lien |
| `ResetPasswordScreen` | Token (deep link) + nouveau mot de passe |
| `EmailVerificationScreen` | Confirmation que l'email de vérification a été envoyé |

---

### Écrans utilisateur standard

#### Home / Dashboard
| Écran | Description |
|-------|-------------|
| `HomeScreen` | Stats globales, mes stats, accès rapide |
| `NotificationsScreen` | Liste des notifs, badge compteur |

#### Déchets
| Écran | Description |
|-------|-------------|
| `MyListingsScreen` | Liste de mes listings avec statut |
| `ListingDetailScreen` | Détail, analyse IA, bouton demande de ramassage |
| `CreateListingScreen` | Formulaire multipart : photo (caméra/galerie), catégorie, quantité, adresse |
| `AIAnalysisPreviewScreen` | Résultat analyse IA avant soumission (valeur estimée, catégorie suggérée) |
| `EditListingScreen` | Modification d'un listing |

#### Ramassages
| Écran | Description |
|-------|-------------|
| `MyPickupsScreen` | Liste de mes demandes avec statuts |
| `PickupDetailScreen` | Détail, historique des statuts, infos collecteur, carte |
| `CreatePickupScreen` | Formulaire : adresse (+ carte), date, créneau, instructions |

#### Marketplace
| Écran | Description |
|-------|-------------|
| `MarketplaceScreen` | Liste enchères actives, filtres, barre de recherche |
| `AuctionDetailScreen` | Détail enchère, countdown, offres, bouton bid / buy-now |
| `PlaceBidBottomSheet` | Saisie montant d'enchère |
| `CreateAuctionScreen` | Créer une enchère sur un listing approuvé |
| `MyOrdersScreen` | Mes commandes acheteur |
| `MySalesScreen` | Mes ventes |
| `OrderDetailScreen` | Détail commande + statut paiement |
| `PaymentCheckoutScreen` | Sélection mode de paiement |
| `StripeCheckoutScreen` | flutter_stripe PaymentSheet |
| `PlopPlopCheckoutScreen` | WebView PlopPlop → retour app |
| `PaymentSuccessScreen` | Confirmation de paiement |

#### Academy
| Écran | Description |
|-------|-------------|
| `AcademyScreen` | Catalogue cours (filtres, recherche) |
| `CourseDetailScreen` | Description, leçons, progression, bouton inscription/paiement |
| `LessonScreen` | Contenu : Markdown, vidéo (YouTube / Vimeo / TikTok / Instagram / MP4), PDF |
| `MyCoursesScreen` | Mes cours en cours avec barre de progression |
| `MyCertificatesScreen` | Liste de mes certificats, bouton télécharger PDF |
| `CoursePaymentScreen` | Sélection Stripe / PlopPlop pour un cours payant |

#### Impact
| Écran | Description |
|-------|-------------|
| `ImpactDashboardScreen` | Mes stats, graphiques, historique |
| `LeaderboardScreen` | Top 20 recycleurs |

#### Profil
| Écran | Description |
|-------|-------------|
| `ProfileScreen` | Infos profil, photo avatar |
| `EditProfileScreen` | Modifier prénom, nom, téléphone, bio, ville, adresse, avatar |
| `ChangePasswordScreen` | Ancien mdp + nouveau mdp |
| `SettingsScreen` | Langue, notifications, déconnexion |

#### Divers
| Écran | Description |
|-------|-------------|
| `BlogListScreen` | Liste articles |
| `BlogPostScreen` | Lecture article (Markdown/HTML) |
| `ContactScreen` | Formulaire de contact |

---

### Écrans collecteur (en plus)

| Écran | Description |
|-------|-------------|
| `CollectorDashboardScreen` | Ramassages assignés, stats collecteur |
| `CollectorPickupListScreen` | Liste ramassages actifs assignés (filtre statut) |
| `CollectorPickupDetailScreen` | Détail + boutons de changement de statut + saisie poids |
| `CollectorMapScreen` | Carte des ramassages assignés |

---

### Écrans admin (en plus)

| Écran | Description |
|-------|-------------|
| `AdminDashboardScreen` | Stats globales (`/api/admin/stats/`), alertes |
| `AdminListingsScreen` | Tous les listings (filtre, recherche, approbation) |
| `AdminListingReviewScreen` | Approuver / Rejeter + raison |
| `AdminPickupsScreen` | Tous les ramassages (filtre, recherche) |
| `AdminPickupAssignScreen` | Assigner un collecteur (liste via `/api/admin/collectors/`) |
| `AdminOrdersScreen` | Toutes les commandes |
| `AdminUsersScreen` | Tous les utilisateurs (`/api/admin/users/`) — modifier rôle, activer/désactiver |
| `AdminUserDetailScreen` | Détail utilisateur + formulaire PATCH |
| `AdminAcademyCoursesScreen` | Liste cours admin (`/api/academy/admin/courses/`) |
| `AdminCourseFormScreen` | Créer / modifier un cours |
| `AdminLessonsScreen` | Liste leçons admin (`/api/academy/admin/lessons/`) |
| `AdminLessonFormScreen` | Créer / modifier une leçon |
| `AdminVideoFormScreen` | Ajouter une vidéo à une leçon |

---

## 7. Modèles de données clés

### User
```dart
class User {
  String id;          // UUID
  String email;
  String firstName;
  String lastName;
  String fullName;    // ReadOnly
  String phone;
  String role;        // "user" | "collector" | "admin"
  String? avatar;     // URL
  String? bio;
  String? address;
  String? city;
  bool isEmailVerified;
  int totalListings;
  double totalKgRecycled;
  DateTime createdAt;
}
```

### WasteListing
```dart
class WasteListing {
  String id;          // UUID
  String userId;
  String? categoryId;
  String categoryName;
  String title;
  String description;
  double quantityKg;
  String? photo;      // URL
  Map? aiAnalysis;    // { category_slug, estimated_value_htg, ... }
  double? aiEstimatedValue;
  String pickupAddress;
  String city;
  double? latitude;
  double? longitude;
  String status;      // "pending_review" | "approved" | "rejected" | "sold"
  String? rejectionReason;
  DateTime createdAt;
}
```

### PickupRequest
```dart
class PickupRequest {
  String id;          // UUID
  String userId;
  String? listingId;
  String? collectorId;
  String address;
  String city;
  double? latitude;
  double? longitude;
  String preferredDate; // "YYYY-MM-DD"
  String preferredSlot; // "morning" | "afternoon" | "evening"
  String? specialInstructions;
  String status;        // voir tableau statuts
  List statusHistory;   // [{ status, note, timestamp }]
  double? actualWeightKg;
  String? collectorNotes;
  DateTime createdAt;
}
```

### Auction
```dart
class Auction {
  String id;          // UUID
  WasteListing listing;
  String sellerId;
  String sellerName;
  String auctionType; // "auction" | "buy_now" | "both"
  double startingPrice;
  double? buyNowPrice;
  double currentPrice;
  double? reservePrice;
  String status;      // "active" | "sold" | "closed"
  DateTime startsAt;
  DateTime endsAt;
  int timeRemaining;  // secondes
  int totalBids;
  List<Bid> latestBids;
  Bid? userBid;       // null si pas connecté ou pas enchéri
}
```

### LessonVideo
```dart
class LessonVideo {
  String id;            // UUID
  String title;
  String? videoFile;    // URL fichier direct (null si embed)
  String? videoUrl;     // URL source originale (YouTube, TikTok, etc.)
  String? embedUrl;     // URL d'intégration calculée par le backend
  String platform;      // "youtube" | "vimeo" | "tiktok" | "instagram" | "direct" | "unknown"
  bool allowDownload;
  int durationMinutes;
  int order;
}
```

### Lesson
```dart
class Lesson {
  String id;              // UUID
  String title;
  String content;         // Markdown
  String pdfDisplayMode;  // "extract" | "viewer"
  bool pdfAllowDownload;
  int order;
  int durationMinutes;
  List<LessonVideo> videos;
}
```

### Enrollment (Academy)
```dart
class Enrollment {
  String id;          // UUID
  String courseId;
  String courseTitle;
  String courseSlug;
  int progressPercent;
  bool isCompleted;
  List<String> completedLessonIds;
  String paymentStatus; // "free" | "pending" | "paid"
  DateTime enrolledAt;
  DateTime? completedAt;
}
```

### Notification
```dart
class AppNotification {
  String id;          // UUID
  String notificationType;
  String typeDisplay;
  String title;
  String message;
  Map data;           // contient les IDs pour navigation
  bool isRead;
  DateTime createdAt;
}
```

---

## 8. Notes d'implémentation Flutter

### Lecture vidéo selon plateforme

Le backend retourne `platform` et `embed_url` dans chaque `LessonVideo`. Utiliser la stratégie suivante :

| `platform` | Solution Flutter |
|------------|----------------|
| `youtube` | `youtube_player_flutter` avec `embed_url` |
| `vimeo` | `flutter_inappwebview` avec `embed_url` |
| `tiktok` | `flutter_inappwebview` avec `embed_url` (ratio portrait) |
| `instagram` | `flutter_inappwebview` avec `embed_url` (ratio portrait) |
| `direct` | `video_player` + `chewie` avec `video_file` |

```dart
Widget buildVideoPlayer(LessonVideo video) {
  switch (video.platform) {
    case 'youtube':
      final videoId = YoutubePlayer.convertUrlToId(video.videoUrl ?? '');
      return YoutubePlayer(controller: YoutubePlayerController(initialVideoId: videoId!));
    case 'vimeo':
    case 'tiktok':
    case 'instagram':
      return InAppWebView(initialUrlRequest: URLRequest(url: Uri.parse(video.embedUrl!)));
    case 'direct':
      return VideoPlayer(VideoPlayerController.network(video.videoFile!));
    default:
      return Text('Vidéo non disponible');
  }
}
```

### Paiement cours — Stripe

```dart
// 1. Initialiser le PaymentIntent côté backend
final res = await api.post('/api/academy/courses/$slug/pay/stripe/init/');
final clientSecret      = res['client_secret'];
final transactionNumber = res['transaction_number'];

// 2. Présenter la feuille de paiement Stripe
await Stripe.instance.initPaymentSheet(
  paymentSheetParameters: SetupPaymentSheetParameters(
    paymentIntentClientSecret: clientSecret,
    merchantDisplayName: 'EcoCycle Haiti',
  ),
);
await Stripe.instance.presentPaymentSheet();

// 3. Confirmer côté backend (obligatoire pour activer l'enrollment)
final pi = await Stripe.instance.retrievePaymentIntent(clientSecret);
final enrollment = await api.post(
  '/api/academy/courses/$slug/pay/stripe/confirm/',
  {'payment_intent_id': pi.id},
);
```

### Paiement cours — PlopPlop (MonCash, NatCash, Kashpaw)

```dart
// 1. Créer le paiement
final res = await api.post(
  '/api/academy/courses/$slug/pay/plopplop/',
  {'method': 'moncash'},
);
final redirectUrl      = res['redirect_url'];
final transactionNumber = res['transaction_number'];

// 2. Ouvrir WebView PlopPlop
// Détecter la navigation vers l'URL de retour (contient ?reference_id=...)

// 3. Vérifier le paiement (l'endpoint est public, pas besoin de JWT)
final verify = await api.get(
  '/api/academy/courses/$slug/pay/plopplop/retour/?reference_id=$transactionNumber',
);
// verify['status'] == 'paid' ou 'already_paid'
```

### Countdown temps réel des enchères

```dart
// Utiliser time_remaining (secondes) retourné par l'API
// + un Timer qui décrémente localement sans requête réseau
// Rafraîchir depuis l'API toutes les 30s
Timer.periodic(Duration(seconds: 1), (_) {
  setState(() => timeRemaining--);
  if (timeRemaining <= 0) fetchAuctionDetail();
});
```

### Rafraîchissement automatique

| Contexte | Stratégie |
|----------|-----------|
| Enchères actives | Pull-to-refresh + polling 30s |
| Détail enchère ouverte | Polling 10s |
| Notifications | FCM push (temps réel) + badge mis à jour |
| Statut ramassage | FCM push + pull-to-refresh |

### Gestion des images uploadées

```
MEDIA_URL = https://ecoc.up.railway.app/media/
```
Les champs `photo`, `avatar`, `thumbnail` retournent des chemins relatifs (ex: `courses/thumb.jpg`).
Construire l'URL complète côté client : `BASE_URL + '/media/' + path`.

### Permissions requises

| Permission | Usage |
|------------|-------|
| Camera | Photo listing, photo avatar |
| Photo Library | Sélection photo listing/avatar |
| Location | Adresse de ramassage (optionnel, si géoloc auto) |
| Notifications | Push FCM |

---

*Document mis à jour le 2026-05-20 — tous les endpoints backend sont désormais implémentés.*
