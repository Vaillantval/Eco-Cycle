from celery import shared_task


@shared_task(name='marketplace.close_expired_auctions')
def close_expired_auctions():
    from django.utils import timezone
    from django.db import transaction
    from .models import Auction, Order

    expired_ids = list(
        Auction.objects.filter(status='active', ends_at__lte=timezone.now())
        .values_list('id', flat=True)
    )

    for auction_id in expired_ids:
        try:
            with transaction.atomic():
                auction = (
                    Auction.objects
                    .select_for_update()
                    .select_related('seller', 'listing')
                    .get(id=auction_id, status='active')
                )

                winning_bid = auction.bids.filter(is_winning=True).order_by('-amount').first()

                reserve_met = (
                    not auction.reserve_price
                    or (winning_bid and winning_bid.amount >= auction.reserve_price)
                )

                if winning_bid and reserve_met:
                    auction.status = 'sold'
                    auction.winner = winning_bid.bidder
                    auction.save(update_fields=['status', 'winner', 'updated_at'])

                    auction.listing.status = 'sold'
                    auction.listing.save(update_fields=['status', 'updated_at'])

                    order = Order.objects.create(
                        auction=auction,
                        buyer=winning_bid.bidder,
                        seller=auction.seller,
                        amount=winning_bid.amount,
                    )

                    from apps.notifications.tasks import notify_auction_closed, notify_order_created
                    notify_auction_closed.delay(str(auction.id), winner=True)
                    notify_order_created.delay(str(order.id))

                    from apps.impact.tasks import create_impact_record
                    create_impact_record.delay(str(order.id))

                else:
                    auction.status = 'closed'
                    auction.save(update_fields=['status', 'updated_at'])

                    from apps.notifications.tasks import notify_auction_closed
                    notify_auction_closed.delay(str(auction.id), winner=False)

        except Auction.DoesNotExist:
            # Already processed by another worker
            pass
        except Exception as exc:
            import logging
            logging.getLogger(__name__).error(
                'Error closing auction %s: %s', auction_id, exc, exc_info=True
            )
