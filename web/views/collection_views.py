from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from web.mixins import LoginRequiredMixin
from apps.collections.models import PickupRequest
from apps.waste.models import WasteListing


class MyPickupsView(LoginRequiredMixin, View):
    def get(self, request):
        user    = self.get_current_user(request)
        pickups = PickupRequest.objects.filter(user=user).order_by('-created_at')
        return render(request, 'dashboard/pickups.html', {
            'user': user,
            'pickups': pickups,
        })


class RequestPickupView(LoginRequiredMixin, View):
    def get(self, request):
        from django.utils import timezone
        user          = self.get_current_user(request)
        user_listings = WasteListing.objects.filter(user=user, status='approved')
        return render(request, 'dashboard/request_pickup.html', {
            'user': user,
            'user_listings': user_listings,
            'today': timezone.localdate().isoformat(),
        })

    def post(self, request):
        user = self.get_current_user(request)

        preferred_date = request.POST.get('preferred_date')
        if not preferred_date:
            messages.error(request, 'La date souhaitée est requise.')
            return redirect('request_pickup')

        pickup = PickupRequest.objects.create(
            user=user,
            address=request.POST.get('address', ''),
            city=request.POST.get('city', ''),
            preferred_date=preferred_date,
            preferred_slot=request.POST.get('preferred_slot', 'morning'),
            special_instructions=request.POST.get('special_instructions', ''),
            listing_id=request.POST.get('listing_id') or None,
        )

        from apps.notifications.tasks import notify_admin_new_pickup
        notify_admin_new_pickup.delay(str(pickup.id))

        messages.success(request, 'Demande de ramassage soumise ! Un collecteur sera assigné bientôt.')
        return redirect('my_pickups')


class PickupDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        user   = self.get_current_user(request)
        pickup = get_object_or_404(PickupRequest, pk=pk, user=user)
        return render(request, 'dashboard/pickup_detail.html', {
            'user': user,
            'pickup': pickup,
            'timeline_steps': [
                ('requested',  'Demandé'),
                ('assigned',   'Assigné'),
                ('in_transit', 'En transit'),
                ('arrived',    'Arrivé'),
                ('completed',  'Complété'),
            ],
        })
