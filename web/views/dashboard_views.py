from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from web.mixins import LoginRequiredMixin
from apps.waste.models import WasteListing, WasteCategory
from apps.marketplace.models import Order, Auction
from apps.impact.models import UserImpactSummary, ImpactRecord
from apps.notifications.models import Notification
from apps.academy.models import Certificate


class DashboardOverviewView(LoginRequiredMixin, View):
    def get(self, request):
        from django.utils import timezone
        user = self.get_current_user(request)
        summary, _ = UserImpactSummary.objects.get_or_create(user=user)
        notifications   = Notification.objects.filter(user=user, is_read=False)[:5]
        recent_listings = WasteListing.objects.filter(user=user).order_by('-created_at')[:5]
        active_auctions = (
            Auction.objects
            .filter(seller=user, status='active', ends_at__gt=timezone.now())
            .select_related('listing', 'listing__category')
            .order_by('ends_at')
        )

        return render(request, 'dashboard/overview.html', {
            'user': user,
            'summary': summary,
            'notifications': notifications,
            'recent_listings': recent_listings,
            'active_auctions': active_auctions,
            'listings_count': WasteListing.objects.filter(user=user).count(),
            'pending_count':  WasteListing.objects.filter(user=user, status='pending_review').count(),
        })


class MyListingsView(LoginRequiredMixin, View):
    def get(self, request):
        user          = self.get_current_user(request)
        status_filter = request.GET.get('status', '')
        listings = WasteListing.objects.filter(user=user).select_related('category', 'auction').order_by('-created_at')
        if status_filter:
            listings = listings.filter(status=status_filter)
        return render(request, 'dashboard/my_listings.html', {
            'user': user,
            'listings': listings,
            'status_filter': status_filter,
            'listing_statuses': WasteListing.STATUS_CHOICES,
        })


class SubmitWasteView(LoginRequiredMixin, View):
    def get(self, request):
        user       = self.get_current_user(request)
        categories = WasteCategory.objects.filter(is_active=True)
        return render(request, 'dashboard/submit_waste.html', {
            'user': user,
            'categories': categories,
        })

    def post(self, request):
        user = self.get_current_user(request)
        listing = WasteListing.objects.create(
            user=user,
            title=request.POST.get('title', ''),
            description=request.POST.get('description', ''),
            category_id=request.POST.get('category') or None,
            quantity_kg=request.POST.get('quantity_kg') or 1,
            photo=request.FILES.get('photo'),
            pickup_address=request.POST.get('pickup_address', ''),
            city=request.POST.get('city', ''),
            status='pending_review',
        )
        from apps.waste.tasks import analyze_waste_photo_async, notify_admin_new_listing
        analyze_waste_photo_async.delay(str(listing.id))
        notify_admin_new_listing.delay(str(listing.id))
        messages.success(request, "Déchet soumis ! L'analyse IA est en cours.")
        return redirect('my_listings')


class MyOrdersView(LoginRequiredMixin, View):
    def get(self, request):
        user   = self.get_current_user(request)
        orders = Order.objects.filter(buyer=user).select_related(
            'auction', 'auction__listing', 'seller'
        ).order_by('-created_at')
        return render(request, 'dashboard/my_orders.html', {
            'user': user,
            'orders': orders,
        })


class MyImpactView(LoginRequiredMixin, View):
    def get(self, request):
        user          = self.get_current_user(request)
        summary, _    = UserImpactSummary.objects.get_or_create(user=user)
        records       = ImpactRecord.objects.filter(user=user).order_by('-created_at')[:20]
        return render(request, 'dashboard/my_impact.html', {
            'user': user,
            'summary': summary,
            'records': records,
        })


class MyCertificatesView(LoginRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        certs = Certificate.objects.filter(user=user).select_related('course').order_by('-issued_at')
        return render(request, 'dashboard/my_certificates.html', {
            'user': user,
            'certificates': certs,
        })


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        return render(request, 'dashboard/profile.html', {'user': user})

    def post(self, request):
        user   = self.get_current_user(request)
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
            old_pwd = request.POST.get('old_password', '')
            new_pwd = request.POST.get('new_password', '')
            confirm = request.POST.get('password_confirm', '')
            if not user.check_password(old_pwd):
                messages.error(request, 'Mot de passe actuel incorrect.')
            elif new_pwd != confirm or len(new_pwd) < 8:
                messages.error(request, 'Nouveau mot de passe invalide (8 caractères minimum).')
            else:
                user.set_password(new_pwd)
                user.save()
                messages.success(request, 'Mot de passe modifié.')

        return redirect('profile')
