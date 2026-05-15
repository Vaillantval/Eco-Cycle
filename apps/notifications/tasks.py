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
    bid = Bid.objects.select_related('auction', 'auction__seller', 'bidder').get(id=bid_id)
    auction = bid.auction
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


@shared_task(name='notifications.notify_auction_closed')
def notify_auction_closed(auction_id: str, winner: bool):
    from apps.marketplace.models import Auction
    from .email_service import EmailService
    from .fcm_service import FCMService
    auction = Auction.objects.select_related('winner', 'seller', 'listing').get(id=auction_id)
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


@shared_task(name='notifications.notify_pickup_status_update')
def notify_pickup_status_update(pickup_id: str):
    from apps.collections.models import PickupRequest
    from .fcm_service import FCMService
    pickup = PickupRequest.objects.select_related('user').get(id=pickup_id)
    status_titles = {
        'in_transit': 'Le collecteur est en route !',
        'arrived': 'Le collecteur est arrive',
        'completed': 'Ramassage complete !',
        'failed': 'Ramassage echoue',
    }
    title = status_titles.get(pickup.status, 'Mise a jour du ramassage')
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
