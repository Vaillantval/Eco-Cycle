from celery import shared_task
from .models import Notification


def _create_notification(user, notif_type, title, message, data=None):
    Notification.objects.create(
        user=user,
        notification_type=notif_type,
        title=title,
        message=message,
        data=data or {},
    )


@shared_task(name='notifications.notify_listing_approved')
def notify_listing_approved(listing_id: str):
    from apps.waste.models import WasteListing
    from .email_service import EmailService
    from .fcm_service import FCMService
    listing = WasteListing.objects.select_related('user').get(id=listing_id)
    _create_notification(
        listing.user, 'listing_approved',
        'Listing approuve',
        f'Votre listing "{listing.title}" a ete approuve et est maintenant sur la marketplace.',
        {'listing_id': str(listing.id)},
    )
    EmailService.send_listing_approved(listing)
    FCMService.send_to_user(
        listing.user,
        'Listing approuve !',
        f'"{listing.title}" est maintenant en ligne sur la marketplace.',
        {'type': 'listing_approved', 'listing_id': str(listing.id)},
    )


@shared_task(name='notifications.notify_listing_rejected')
def notify_listing_rejected(listing_id: str):
    from apps.waste.models import WasteListing
    from .email_service import EmailService
    from .fcm_service import FCMService
    listing = WasteListing.objects.select_related('user').get(id=listing_id)
    _create_notification(
        listing.user, 'listing_rejected',
        'Listing non approuve',
        f'Votre listing "{listing.title}" n\'a pas ete approuve. Raison: {listing.rejection_reason}',
        {'listing_id': str(listing.id)},
    )
    EmailService.send_listing_rejected(listing)
    FCMService.send_to_user(
        listing.user,
        'Listing non approuve',
        f'Voir les details pour "{listing.title}".',
        {'type': 'listing_rejected', 'listing_id': str(listing.id)},
    )


@shared_task(name='notifications.notify_new_bid')
def notify_new_bid(bid_id: str):
    from apps.marketplace.models import Bid
    from .fcm_service import FCMService
    bid = Bid.objects.select_related('auction', 'auction__seller', 'auction__listing', 'bidder').get(id=bid_id)
    auction = bid.auction
    # Notifier le vendeur
    FCMService.send_to_user(
        auction.seller,
        'Nouvelle enchere !',
        f'{bid.bidder.full_name} a encheri {bid.amount} HTG sur "{auction.listing.title}".',
        {'type': 'new_bid', 'auction_id': str(auction.id)},
    )
    _create_notification(
        auction.seller, 'new_bid',
        'Nouvelle enchere',
        f'{bid.bidder.full_name} — {bid.amount} HTG',
        {'auction_id': str(auction.id), 'bid_id': str(bid.id)},
    )
    # U2 — Notifier le précédent enchérisseur (surenchéri)
    prev_bid = (
        auction.bids
        .exclude(id=bid.id)
        .exclude(bidder=bid.bidder)
        .order_by('-amount')
        .select_related('bidder')
        .first()
    )
    if prev_bid:
        FCMService.send_to_user(
            prev_bid.bidder,
            'Vous avez été surenchéri !',
            f'Une offre de {bid.amount} HTG dépasse la vôtre sur "{auction.listing.title}".',
            {'type': 'outbid', 'auction_id': str(auction.id)},
        )
        _create_notification(
            prev_bid.bidder, 'outbid',
            'Surenchère !',
            f'{bid.amount} HTG sur « {auction.listing.title} »',
            {'auction_id': str(auction.id)},
        )


@shared_task(name='notifications.notify_auction_closed')
def notify_auction_closed(auction_id: str, winner: bool):
    from apps.marketplace.models import Auction
    from .email_service import EmailService
    from .fcm_service import FCMService
    auction = Auction.objects.select_related('winner', 'seller', 'listing').prefetch_related('bids__bidder').get(id=auction_id)
    if winner and auction.winner:
        FCMService.send_to_user(
            auction.winner,
            'Vous avez gagne !',
            f'Vous avez remporte l\'enchere pour "{auction.listing.title}" — {auction.current_price} HTG.',
            {'type': 'auction_won', 'auction_id': str(auction_id)},
        )
        _create_notification(
            auction.winner, 'auction_won',
            'Enchere gagnee !',
            f'"{auction.listing.title}" — {auction.current_price} HTG',
            {'auction_id': str(auction_id)},
        )
        if hasattr(auction, 'order'):
            EmailService.send_auction_won(auction.order)
        # U6 — Notifier les enchérisseurs perdants
        losing_bidders = (
            auction.bids
            .exclude(bidder=auction.winner)
            .values_list('bidder', flat=True)
            .distinct()
        )
        from apps.accounts.models import User as _User
        losers = list(_User.objects.filter(id__in=losing_bidders))
        FCMService.send_to_multiple(
            losers,
            'Enchère terminée',
            f'Vous n\'avez pas remporté « {auction.listing.title} ». Continuez d\'explorer la marketplace.',
            {'type': 'auction_lost', 'auction_id': str(auction_id)},
        )
        for loser in losers:
            _create_notification(
                loser, 'auction_lost',
                'Enchère non remportée',
                f'« {auction.listing.title} » a été vendu à {auction.current_price} HTG.',
                {'auction_id': str(auction_id)},
            )
    else:
        # No winner — notify the seller
        FCMService.send_to_user(
            auction.seller,
            'Enchere cloturee sans acheteur',
            f'Votre annonce "{auction.listing.title}" n\'a recu aucune offre valide.',
            {'type': 'auction_closed', 'auction_id': str(auction_id)},
        )
        _create_notification(
            auction.seller, 'auction_closed',
            'Enchere cloturee',
            f'"{auction.listing.title}" — aucune offre valide.',
            {'auction_id': str(auction_id)},
        )


@shared_task(name='notifications.notify_order_created')
def notify_order_created(order_id: str):
    from apps.marketplace.models import Order
    from .email_service import EmailService
    from .fcm_service import FCMService
    order = Order.objects.select_related('buyer', 'seller', 'auction__listing').get(id=order_id)
    _create_notification(
        order.buyer, 'order_created',
        'Commande confirmee',
        f'Votre achat de "{order.auction.listing.title}" est confirme — {order.amount} HTG.',
        {'order_id': str(order.id)},
    )
    FCMService.send_to_user(
        order.buyer,
        'Commande confirmee',
        f'"{order.auction.listing.title}" — {order.amount} HTG.',
        {'type': 'order_created', 'order_id': str(order.id)},
    )


@shared_task(name='notifications.notify_order_paid')
def notify_order_paid(order_id: str):
    """Déclenché quand le paiement est confirmé — notifie acheteur + vendeur + crée l'impact record."""
    from apps.marketplace.models import Order
    from apps.notifications.email_service import EmailService
    from .fcm_service import FCMService
    order = Order.objects.select_related('buyer', 'seller', 'auction__listing').get(id=order_id)

    # Notification in-app acheteur
    _create_notification(
        order.buyer, 'order_paid',
        'Paiement confirmé !',
        f'Votre paiement pour "{order.auction.listing.title}" a été reçu — {order.amount} HTG.',
        {'order_id': str(order.id)},
    )
    # Notification in-app vendeur
    _create_notification(
        order.seller, 'order_paid',
        'Votre article a été vendu !',
        f'"{order.auction.listing.title}" — vous recevrez {order.seller_payout} HTG.',
        {'order_id': str(order.id)},
    )
    # Push acheteur
    FCMService.send_to_user(
        order.buyer,
        '✅ Paiement confirmé !',
        f'{order.auction.listing.title} — {order.amount} HTG',
        {'type': 'order_paid', 'order_id': str(order.id)},
    )
    # Push vendeur
    FCMService.send_to_user(
        order.seller,
        '💰 Article vendu !',
        f'{order.auction.listing.title} — {order.seller_payout} HTG vous seront versés.',
        {'type': 'order_sold', 'order_id': str(order.id)},
    )
    # Email vendeur
    try:
        EmailService.send_order_paid_seller(order)
    except Exception:
        pass
    # Impact record (maintenant que le paiement est réel)
    from apps.impact.tasks import create_impact_record
    create_impact_record.delay(str(order.id))


@shared_task(name='notifications.notify_admin_new_pickup')
def notify_admin_new_pickup(pickup_id: str):
    from apps.collections.models import PickupRequest
    from apps.accounts.models import User
    from .fcm_service import FCMService
    pickup = PickupRequest.objects.select_related('user').get(id=pickup_id)
    admins = User.objects.filter(role='admin', is_active=True)
    FCMService.send_to_multiple(
        list(admins),
        'Nouvelle demande de ramassage',
        f'{pickup.user.full_name} — {pickup.city}, {pickup.preferred_date}',
        {'type': 'new_pickup', 'pickup_id': str(pickup_id)},
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
            'Nouveau ramassage assigne',
            f'Ramassage chez {pickup.user.full_name} — {pickup.city}, {pickup.preferred_date}',
            {'type': 'pickup_assigned', 'pickup_id': str(pickup_id)},
        )
    FCMService.send_to_user(
        pickup.user,
        'Ramassage confirme',
        f'Un collecteur a ete assigne a votre demande du {pickup.preferred_date}.',
        {'type': 'pickup_confirmed', 'pickup_id': str(pickup_id)},
    )
    EmailService.send_pickup_confirmed(pickup)


@shared_task(name='notifications.notify_course_completed')
def notify_course_completed(user_id: str, course_id: str, cert_id: str):
    from apps.accounts.models import User
    from apps.academy.models import Course, Certificate
    from .email_service import EmailService
    from .fcm_service import FCMService
    user = User.objects.get(id=user_id)
    course = Course.objects.get(id=course_id)
    cert = Certificate.objects.get(id=cert_id)
    EmailService.send_certificate_earned(user, course, cert)
    # U5 — Push FCM au user
    FCMService.send_to_user(
        user,
        'Certificat disponible !',
        f'Vous avez terminé « {course.title} ». Votre certificat est prêt !',
        {'type': 'course_completed', 'course_id': str(course.id), 'cert_id': str(cert.id)},
    )
    for admin in User.objects.filter(role='admin', is_active=True):
        EmailService.send_admin_course_completed(admin, user, course, cert)


@shared_task(name='notifications.notify_contact_message')
def notify_contact_message(message_id: int):
    from apps.core.models import ContactMessage
    from apps.accounts.models import User
    from .email_service import EmailService
    msg = ContactMessage.objects.get(id=message_id)
    html = (
        f'<p><strong>De :</strong> {msg.first_name} {msg.last_name} ({msg.email})</p>'
        f'<p><strong>Sujet :</strong> {msg.subject}</p>'
        f'<p>{msg.message}</p>'
    )
    for admin in User.objects.filter(role='admin', is_active=True):
        EmailService._send(admin.email, f'[EcoCycle Contact] {msg.subject}', html)


@shared_task(name='notifications.notify_newsletter_signup')
def notify_newsletter_signup(subscriber_id: int):
    from apps.core.models import NewsletterSubscriber
    from .email_service import EmailService
    subscriber = NewsletterSubscriber.objects.get(id=subscriber_id)
    EmailService.send_newsletter_confirmation(subscriber)


@shared_task(name='notifications.notify_admin_new_user')
def notify_admin_new_user(user_id: str):
    from apps.accounts.models import User
    from .email_service import EmailService
    from .fcm_service import FCMService
    try:
        new_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return
    admins = list(User.objects.filter(role='admin', is_active=True))
    for admin in admins:
        EmailService.send_admin_new_user(admin, new_user)
    FCMService.send_to_multiple(
        admins,
        'Nouvel utilisateur inscrit',
        f'{new_user.full_name} ({new_user.email})',
        {'type': 'admin_new_user', 'user_id': str(new_user.id)},
    )


@shared_task(name='notifications.notify_admin_payment_received')
def notify_admin_payment_received(transaction_id: str):
    from apps.payments.models import Transaction
    from apps.accounts.models import User
    from .email_service import EmailService
    from .fcm_service import FCMService
    try:
        transaction = Transaction.objects.select_related(
            'order__buyer', 'order__auction__listing',
            'enrollment__user', 'enrollment__course',
        ).get(id=transaction_id)
    except Transaction.DoesNotExist:
        return
    admins = list(User.objects.filter(role='admin', is_active=True))
    for admin in admins:
        EmailService.send_admin_payment_received(admin, transaction)
    if transaction.order_id:
        label = transaction.order.auction.listing.title
        buyer_name = transaction.order.buyer.full_name
    else:
        label = transaction.enrollment.course.title
        buyer_name = transaction.enrollment.user.full_name
    FCMService.send_to_multiple(
        admins,
        'Paiement reçu',
        f'{buyer_name} — {transaction.amount} HTG — {label}',
        {'type': 'admin_payment_received', 'transaction_id': str(transaction.id)},
    )


@shared_task(name='notifications.notify_admin_pickup_failed')
def notify_admin_pickup_failed(pickup_id: str):
    from apps.collections.models import PickupRequest
    from apps.accounts.models import User
    from .email_service import EmailService
    from .fcm_service import FCMService
    try:
        pickup = PickupRequest.objects.select_related('user', 'collector').get(id=pickup_id)
    except PickupRequest.DoesNotExist:
        return
    admins = list(User.objects.filter(role='admin', is_active=True))
    for admin in admins:
        EmailService.send_admin_pickup_failed(admin, pickup)
    collector_name = pickup.collector.full_name if pickup.collector else 'Collecteur inconnu'
    FCMService.send_to_multiple(
        admins,
        'Ramassage échoué',
        f'{pickup.user.full_name} — {pickup.city} — {collector_name}',
        {'type': 'admin_pickup_failed', 'pickup_id': str(pickup.id)},
    )


@shared_task(name='notifications.notify_admin_paid_enrollment')
def notify_admin_paid_enrollment(enrollment_id: str):
    from apps.academy.models import Enrollment
    from apps.accounts.models import User
    from .email_service import EmailService
    from .fcm_service import FCMService
    try:
        enrollment = Enrollment.objects.select_related('user', 'course').get(id=enrollment_id)
    except Enrollment.DoesNotExist:
        return
    admins = list(User.objects.filter(role='admin', is_active=True))
    for admin in admins:
        EmailService.send_admin_paid_enrollment(admin, enrollment)
    FCMService.send_to_multiple(
        admins,
        'Inscription cours payant',
        f'{enrollment.user.full_name} — « {enrollment.course.title} »',
        {'type': 'admin_paid_enrollment', 'enrollment_id': str(enrollment.id)},
    )


@shared_task(name='notifications.notify_pickup_status_update')
def notify_pickup_status_update(pickup_id: str):
    from apps.collections.models import PickupRequest
    from .email_service import EmailService
    from .fcm_service import FCMService
    pickup = PickupRequest.objects.select_related('user').get(id=pickup_id)
    status_titles = {
        'in_transit': 'Le collecteur est en route !',
        'arrived': 'Le collecteur est arrivé',
        'completed': 'Ramassage complété !',
        'failed': 'Ramassage échoué',
    }
    title = status_titles.get(pickup.status, 'Mise à jour du ramassage')
    # U1 — Push FCM
    FCMService.send_to_user(
        pickup.user, title,
        f'Ramassage du {pickup.preferred_date} — {pickup.get_status_display()}',
        {'type': 'pickup_status', 'pickup_id': str(pickup_id), 'status': pickup.status},
    )
    _create_notification(
        pickup.user, 'pickup_status', title,
        pickup.get_status_display(),
        {'pickup_id': str(pickup_id)},
    )
    # U1 — Email pour les statuts importants
    if pickup.status in ('in_transit', 'completed'):
        try:
            EmailService.send_pickup_status_update(pickup)
        except Exception:
            pass


@shared_task(name='notifications.send_lesson_reminders')
def send_lesson_reminders():
    """U4 — Envoi quotidien de rappels aux étudiants qui ont commencé un cours mais ne l'ont pas terminé."""
    from django.utils import timezone
    from apps.academy.models import Enrollment
    from .email_service import EmailService
    from .fcm_service import FCMService
    now = timezone.now()
    # Fenêtre 48h–72h après enrollment : chaque enrollment passe une seule fois dans cette fenêtre
    window_start = now - timezone.timedelta(hours=72)
    window_end   = now - timezone.timedelta(hours=48)
    stale = Enrollment.objects.filter(
        is_completed=False,
        progress_percent__gt=0,
        enrolled_at__range=(window_start, window_end),
    ).select_related('user', 'course')
    for enrollment in stale:
        try:
            EmailService.send_lesson_reminder(enrollment)
        except Exception:
            pass
        FCMService.send_to_user(
            enrollment.user,
            'Continuez votre apprentissage !',
            f'Reprenez « {enrollment.course.title} » là où vous en étiez.',
            {'type': 'lesson_reminder', 'course_slug': enrollment.course.slug},
        )


@shared_task(name='notifications.notify_new_lesson')
def notify_new_lesson(lesson_id: str):
    """U7 — Notifie par FCM tous les étudiants inscrits quand une nouvelle leçon est ajoutée."""
    from apps.academy.models import Lesson, Enrollment
    from apps.accounts.models import User
    from .fcm_service import FCMService
    try:
        lesson = Lesson.objects.select_related('course').get(id=lesson_id)
    except Lesson.DoesNotExist:
        return
    course = lesson.course
    enrolled_user_ids = Enrollment.objects.filter(
        course=course,
        is_completed=False,
    ).values_list('user_id', flat=True)
    students = list(User.objects.filter(id__in=enrolled_user_ids, is_active=True))
    FCMService.send_to_multiple(
        students,
        'Nouvelle leçon disponible !',
        f'« {lesson.title} » vient d\'être ajoutée à {course.title}.',
        {'type': 'new_lesson', 'course_slug': course.slug, 'lesson_id': str(lesson.id)},
    )
