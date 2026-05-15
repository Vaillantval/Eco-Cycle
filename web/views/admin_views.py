from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from web.mixins import AdminRequiredMixin
from apps.accounts.models import User
from apps.waste.models import WasteListing
from apps.collections.models import PickupRequest
from apps.marketplace.models import Order


class AdminDashboardView(AdminRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        context = {
            'user': user,
            'total_users':       User.objects.count(),
            'total_listings':    WasteListing.objects.count(),
            'pending_listings':  WasteListing.objects.filter(status='pending_review').count(),
            'total_pickups':     PickupRequest.objects.count(),
            'pending_pickups':   PickupRequest.objects.filter(status='requested').count(),
            'total_orders':      Order.objects.count(),
            'recent_listings':   WasteListing.objects.select_related('user', 'category').order_by('-created_at')[:8],
            'recent_pickups':    PickupRequest.objects.select_related('user', 'collector').order_by('-created_at')[:8],
        }
        return render(request, 'admin_panel/dashboard.html', context)


class AdminListingsView(AdminRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        status_filter = request.GET.get('status', '')
        listings = WasteListing.objects.select_related('user', 'category').order_by('-created_at')
        if status_filter:
            listings = listings.filter(status=status_filter)
        return render(request, 'admin_panel/listings.html', {
            'user': user,
            'listings': listings,
            'status_filter': status_filter,
            'status_choices': WasteListing.STATUS_CHOICES,
        })


class AdminReviewListingView(AdminRequiredMixin, View):
    def get(self, request, pk):
        user = self.get_current_user(request)
        listing = get_object_or_404(WasteListing, pk=pk)
        return render(request, 'admin_panel/listing_detail.html', {
            'user': user,
            'listing': listing,
        })

    def post(self, request, pk):
        admin = self.get_current_user(request)
        listing = get_object_or_404(WasteListing, pk=pk)
        action = request.POST.get('action')

        if action == 'approve':
            listing.status = 'approved'
            listing.reviewed_by = admin
            listing.reviewed_at = timezone.now()
            listing.rejection_reason = ''
            listing.save()
            messages.success(request, f'Listing « {listing.title} » approuvé.')
        elif action == 'reject':
            reason = request.POST.get('rejection_reason', '').strip()
            listing.status = 'rejected'
            listing.reviewed_by = admin
            listing.reviewed_at = timezone.now()
            listing.rejection_reason = reason
            listing.save()
            messages.warning(request, f'Listing « {listing.title} » rejeté.')

        return redirect('admin_listings')


class AdminPickupsView(AdminRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        status_filter = request.GET.get('status', '')
        pickups = PickupRequest.objects.select_related('user', 'collector').order_by('-created_at')
        if status_filter:
            pickups = pickups.filter(status=status_filter)
        collectors = User.objects.filter(role='collector', is_active=True).order_by('first_name')
        return render(request, 'admin_panel/pickups.html', {
            'user': user,
            'pickups': pickups,
            'status_filter': status_filter,
            'status_choices': PickupRequest.STATUS_CHOICES,
            'collectors': collectors,
        })

    def post(self, request):
        pickup_id   = request.POST.get('pickup_id')
        collector_id = request.POST.get('collector_id')
        pickup = get_object_or_404(PickupRequest, pk=pickup_id)

        if not collector_id:
            messages.error(request, 'Sélectionner un collecteur.')
            return redirect('admin_pickups')

        collector = get_object_or_404(User, pk=collector_id, role='collector')
        pickup.collector = collector
        pickup.update_status('assigned', f'Assigné à {collector.full_name} via panel admin')
        messages.success(request, f'Ramassage assigné à {collector.full_name}.')
        return redirect('admin_pickups')


class AdminUsersView(AdminRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        role_filter = request.GET.get('role', '')
        users = User.objects.order_by('-created_at')
        if role_filter:
            users = users.filter(role=role_filter)
        return render(request, 'admin_panel/users.html', {
            'user': user,
            'users': users,
            'role_filter': role_filter,
            'role_choices': User.ROLE_CHOICES,
        })

    def post(self, request):
        target_id = request.POST.get('user_id')
        action    = request.POST.get('action')
        target    = get_object_or_404(User, pk=target_id)

        if action == 'toggle_active':
            target.is_active = not target.is_active
            target.save()
            state = 'activé' if target.is_active else 'désactivé'
            messages.success(request, f'Compte de {target.full_name} {state}.')
        elif action == 'change_role':
            new_role = request.POST.get('new_role')
            if new_role in dict(User.ROLE_CHOICES):
                target.role = new_role
                target.save()
                messages.success(request, f'Rôle de {target.full_name} changé en {new_role}.')

        return redirect('admin_users')


class AdminOrdersView(AdminRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        status_filter = request.GET.get('status', '')
        orders = Order.objects.select_related('buyer', 'seller', 'auction__listing').order_by('-created_at')
        if status_filter:
            orders = orders.filter(status=status_filter)
        return render(request, 'admin_panel/orders.html', {
            'user': user,
            'orders': orders,
            'status_filter': status_filter,
            'status_choices': Order.STATUS_CHOICES,
        })
