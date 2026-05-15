from celery import shared_task


@shared_task(name='marketplace.close_expired_auctions')
def close_expired_auctions():
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
