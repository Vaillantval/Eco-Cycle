from celery import shared_task


@shared_task(name='impact.create_impact_record')
def create_impact_record(order_id: str):
    from django.db.models import Sum
    from apps.marketplace.models import Order
    from .models import ImpactRecord, UserImpactSummary, CO2_FACTORS

    order = Order.objects.select_related(
        'buyer', 'auction__listing__category'
    ).get(id=order_id)

    listing = order.auction.listing
    category_slug = listing.category.slug if listing.category else 'other'
    kg = float(listing.quantity_kg or 1.0)
    co2 = kg * CO2_FACTORS.get(category_slug, 0.5)

    ImpactRecord.objects.create(
        user=order.buyer,
        order=order,
        category_slug=category_slug,
        kg_recycled=kg,
        co2_saved_kg=co2,
        economic_value_htg=order.amount,
    )

    summary, _ = UserImpactSummary.objects.get_or_create(user=order.buyer)
    records = ImpactRecord.objects.filter(user=order.buyer)
    agg = records.aggregate(
        total_kg=Sum('kg_recycled'),
        total_co2=Sum('co2_saved_kg'),
        total_value=Sum('economic_value_htg'),
    )
    summary.total_kg_recycled = agg['total_kg'] or 0
    summary.total_co2_saved_kg = agg['total_co2'] or 0
    summary.total_economic_value_htg = agg['total_value'] or 0
    summary.total_transactions = records.count()
    summary.save()

    update_community_rankings.delay()


@shared_task(name='impact.update_community_rankings')
def update_community_rankings():
    from .models import UserImpactSummary
    summaries = UserImpactSummary.objects.order_by('-total_kg_recycled')
    for rank, summary in enumerate(summaries, start=1):
        UserImpactSummary.objects.filter(pk=summary.pk).update(community_rank=rank)
