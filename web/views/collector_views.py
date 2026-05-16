from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from web.mixins import CollectorRequiredMixin
from apps.collections.models import PickupRequest


class CollectorDashboardView(CollectorRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        my_pickups = PickupRequest.objects.filter(collector=user)
        today = timezone.localdate()

        context = {
            'user': user,
            'count_assigned':   my_pickups.filter(status='assigned').count(),
            'count_in_transit': my_pickups.filter(status='in_transit').count(),
            'count_arrived':    my_pickups.filter(status='arrived').count(),
            'count_completed':  my_pickups.filter(status='completed').count(),
            'count_today':      my_pickups.filter(preferred_date=today).count(),
            'active_pickups':   my_pickups.filter(
                status__in=['assigned', 'in_transit', 'arrived']
            ).select_related('user', 'listing').order_by('preferred_date')[:8],
            'recent_completed': my_pickups.filter(
                status='completed'
            ).select_related('user').order_by('-completed_at')[:5],
        }
        return render(request, 'collector/overview.html', context)


class CollectorPickupsView(CollectorRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        status_filter = request.GET.get('status', '')
        qs = PickupRequest.objects.filter(collector=user).select_related('user', 'listing').order_by('-updated_at')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return render(request, 'collector/pickups.html', {
            'user': user,
            'pickups': qs,
            'status_filter': status_filter,
            'status_choices': PickupRequest.STATUS_CHOICES,
        })


class CollectorPickupDetailView(CollectorRequiredMixin, View):
    def get(self, request, pk):
        user = self.get_current_user(request)
        pickup = get_object_or_404(PickupRequest, pk=pk, collector=user)
        return render(request, 'collector/pickup_detail.html', {'user': user, 'pickup': pickup})

    def post(self, request, pk):
        user = self.get_current_user(request)
        pickup = get_object_or_404(PickupRequest, pk=pk, collector=user)
        action = request.POST.get('action')

        if action == 'start_transit' and pickup.status == 'assigned':
            pickup.update_status('in_transit', 'Collecteur en route vers le client')
            messages.success(request, 'En route ! Statut mis à jour.')

        elif action == 'arrive' and pickup.status == 'in_transit':
            pickup.update_status('arrived', 'Collecteur arrivé sur place')
            messages.success(request, 'Arrivée confirmée.')

        elif action == 'complete' and pickup.status == 'arrived':
            weight = request.POST.get('actual_weight_kg', '').strip()
            notes = request.POST.get('collector_notes', '').strip()
            pickup.collector_notes = notes
            if weight:
                try:
                    pickup.actual_weight_kg = float(weight)
                except ValueError:
                    pass
            if request.FILES.get('completion_photo'):
                pickup.completion_photo = request.FILES['completion_photo']
            pickup.update_status('completed', f'Ramassage complété. Poids: {weight or "N/A"} kg. {notes}')
            messages.success(request, 'Ramassage complété avec succès !')

        elif action == 'fail':
            reason = request.POST.get('fail_reason', 'Collecte impossible').strip()
            pickup.update_status('failed', reason)
            messages.warning(request, f'Ramassage marqué comme échoué.')

        return redirect('collector_pickup_detail', pk=pk)


class CollectorProfileView(CollectorRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        all_pickups = PickupRequest.objects.filter(collector=user)
        stats = {
            'total':       all_pickups.count(),
            'completed':   all_pickups.filter(status='completed').count(),
            'in_progress': all_pickups.filter(status__in=['assigned', 'in_transit', 'arrived']).count(),
            'failed':      all_pickups.filter(status='failed').count(),
        }
        return render(request, 'collector/profile.html', {'user': user, 'stats': stats})

    def post(self, request):
        user = self.get_current_user(request)
        action = request.POST.get('action')

        if action == 'update_profile':
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name  = request.POST.get('last_name',  user.last_name)
            user.phone      = request.POST.get('phone',      user.phone)
            user.bio        = request.POST.get('bio',        user.bio)
            user.address    = request.POST.get('address',    user.address)
            user.city       = request.POST.get('city',       user.city)
            if request.FILES.get('avatar'):
                user.avatar = request.FILES['avatar']
            user.save()
            request.session['user_name'] = user.full_name
            messages.success(request, 'Profil mis à jour.')

        elif action == 'change_password':
            old = request.POST.get('old_password', '')
            new = request.POST.get('new_password', '')
            confirm = request.POST.get('password_confirm', '')
            if not user.check_password(old):
                messages.error(request, 'Mot de passe actuel incorrect.')
            elif new != confirm or len(new) < 8:
                messages.error(request, 'Nouveau mot de passe invalide (8 caractères min).')
            else:
                user.set_password(new)
                user.save()
                messages.success(request, 'Mot de passe modifié.')

        return redirect('collector_profile')
