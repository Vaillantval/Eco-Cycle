from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from web.mixins import AdminRequiredMixin
from apps.accounts.models import User
from apps.waste.models import WasteListing
from apps.collections.models import PickupRequest
from apps.marketplace.models import Order, Auction
from apps.blog.models import Post
from apps.academy.models import Course
from apps.core.models import ContactMessage, NewsletterSubscriber, SiteConfiguration


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


class AdminUserDetailView(AdminRequiredMixin, View):
    def get(self, request, pk):
        admin = self.get_current_user(request)
        target = get_object_or_404(User, pk=pk)
        listings = WasteListing.objects.filter(user=target).order_by('-created_at')[:10]
        pickups  = PickupRequest.objects.filter(user=target).order_by('-created_at')[:10]
        orders   = Order.objects.filter(buyer=target).order_by('-created_at')[:10]
        return render(request, 'admin_panel/user_detail.html', {
            'user': admin,
            'target': target,
            'listings': listings,
            'pickups': pickups,
            'orders': orders,
            'role_choices': User.ROLE_CHOICES,
        })

    def post(self, request, pk):
        admin = self.get_current_user(request)
        target = get_object_or_404(User, pk=pk)
        action = request.POST.get('action')

        if action == 'toggle_active':
            if target.pk == admin.pk:
                messages.error(request, 'Vous ne pouvez pas désactiver votre propre compte.')
            else:
                target.is_active = not target.is_active
                target.save()
                state = 'activé' if target.is_active else 'désactivé'
                messages.success(request, f'Compte de {target.full_name} {state}.')
        elif action == 'change_role':
            new_role = request.POST.get('new_role')
            if new_role in dict(User.ROLE_CHOICES) and target.pk != admin.pk:
                target.role = new_role
                target.save()
                messages.success(request, f'Rôle de {target.full_name} changé en {new_role}.')

        return redirect('admin_user_detail', pk=pk)


class AdminPickupDetailView(AdminRequiredMixin, View):
    def get(self, request, pk):
        admin = self.get_current_user(request)
        pickup = get_object_or_404(PickupRequest, pk=pk)
        collectors = User.objects.filter(role='collector', is_active=True).order_by('first_name')
        return render(request, 'admin_panel/pickup_detail.html', {
            'user': admin,
            'pickup': pickup,
            'collectors': collectors,
            'status_choices': PickupRequest.STATUS_CHOICES,
        })

    def post(self, request, pk):
        pickup = get_object_or_404(PickupRequest, pk=pk)
        action = request.POST.get('action')

        if action == 'assign':
            collector_id = request.POST.get('collector_id')
            if collector_id:
                collector = get_object_or_404(User, pk=collector_id, role='collector')
                pickup.collector = collector
                pickup.update_status('assigned', f'Assigné à {collector.full_name} via panel admin')
                messages.success(request, f'Assigné à {collector.full_name}.')
        elif action == 'change_status':
            new_status = request.POST.get('new_status')
            valid = [s for s, _ in PickupRequest.STATUS_CHOICES]
            if new_status in valid:
                note = request.POST.get('note', f'Changement de statut par admin')
                pickup.update_status(new_status, note)
                messages.success(request, f'Statut mis à jour : {new_status}.')

        return redirect('admin_pickup_detail', pk=pk)


class AdminOrderDetailView(AdminRequiredMixin, View):
    def get(self, request, pk):
        admin = self.get_current_user(request)
        order = get_object_or_404(Order, pk=pk)
        return render(request, 'admin_panel/order_detail.html', {
            'user': admin,
            'order': order,
            'status_choices': Order.STATUS_CHOICES,
        })

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        new_status = request.POST.get('new_status')
        valid = [s for s, _ in Order.STATUS_CHOICES]
        if new_status in valid:
            order.status = new_status
            if new_status == 'completed':
                order.completed_at = timezone.now()
            order.save()
            messages.success(request, f'Commande mise à jour : {new_status}.')
        return redirect('admin_order_detail', pk=pk)


class AdminBlogView(AdminRequiredMixin, View):
    def get(self, request):
        admin = self.get_current_user(request)
        status_filter = request.GET.get('status', '')
        posts = Post.objects.select_related('author', 'category').order_by('-created_at')
        if status_filter:
            posts = posts.filter(status=status_filter)
        return render(request, 'admin_panel/blog.html', {
            'user': admin,
            'posts': posts,
            'status_filter': status_filter,
        })

    def post(self, request):
        post_id = request.POST.get('post_id')
        action  = request.POST.get('action')
        post = get_object_or_404(Post, pk=post_id)

        if action == 'publish':
            post.status = 'published'
            post.published_at = timezone.now()
            post.save()
            messages.success(request, f'Article « {post.title} » publié.')
        elif action == 'unpublish':
            post.status = 'draft'
            post.save()
            messages.info(request, f'Article « {post.title} » repassé en brouillon.')
        elif action == 'delete':
            title = post.title
            post.delete()
            messages.warning(request, f'Article « {title} » supprimé.')

        return redirect('admin_blog')


class AdminAcademyView(AdminRequiredMixin, View):
    def get(self, request):
        admin = self.get_current_user(request)
        courses = Course.objects.prefetch_related('lessons', 'enrollments').order_by('-created_at')
        return render(request, 'admin_panel/academy.html', {
            'user': admin,
            'courses': courses,
        })

    def post(self, request):
        course_id = request.POST.get('course_id')
        action    = request.POST.get('action')
        course = get_object_or_404(Course, pk=course_id)

        if action == 'toggle_publish':
            course.is_published = not course.is_published
            course.save()
            state = 'publié' if course.is_published else 'dépublié'
            messages.success(request, f'Cours « {course.title} » {state}.')

        return redirect('admin_academy')


class AdminNewslettersView(AdminRequiredMixin, View):
    def get(self, request):
        admin = self.get_current_user(request)
        confirmed_filter = request.GET.get('confirmed', '')
        subs = NewsletterSubscriber.objects.order_by('-subscribed_at')
        if confirmed_filter == '1':
            subs = subs.filter(is_confirmed=True)
        elif confirmed_filter == '0':
            subs = subs.filter(is_confirmed=False)
        return render(request, 'admin_panel/newsletters.html', {
            'user': admin,
            'subscribers': subs,
            'confirmed_filter': confirmed_filter,
            'total_confirmed': NewsletterSubscriber.objects.filter(is_confirmed=True).count(),
            'total_pending':   NewsletterSubscriber.objects.filter(is_confirmed=False).count(),
        })

    def post(self, request):
        sub_id = request.POST.get('sub_id')
        action = request.POST.get('action')
        sub = get_object_or_404(NewsletterSubscriber, pk=sub_id)
        if action == 'delete':
            sub.delete()
            messages.warning(request, 'Abonné supprimé.')
        return redirect('admin_newsletters')


class AdminContactsView(AdminRequiredMixin, View):
    def get(self, request):
        admin = self.get_current_user(request)
        read_filter = request.GET.get('read', '')
        contacts = ContactMessage.objects.order_by('-created_at')
        if read_filter == '0':
            contacts = contacts.filter(is_read=False)
        elif read_filter == '1':
            contacts = contacts.filter(is_read=True)
        return render(request, 'admin_panel/contacts.html', {
            'user': admin,
            'contacts': contacts,
            'read_filter': read_filter,
            'unread_count': ContactMessage.objects.filter(is_read=False).count(),
        })

    def post(self, request):
        msg_id = request.POST.get('msg_id')
        action = request.POST.get('action')
        msg = get_object_or_404(ContactMessage, pk=msg_id)
        if action == 'mark_read':
            msg.is_read = True
            msg.save()
        elif action == 'mark_replied':
            msg.replied = True
            msg.is_read = True
            msg.save()
            messages.success(request, 'Message marqué comme répondu.')
        elif action == 'delete':
            msg.delete()
            messages.warning(request, 'Message supprimé.')
        return redirect('admin_contacts')


class AdminSiteConfigView(AdminRequiredMixin, View):
    def get(self, request):
        admin = self.get_current_user(request)
        config = SiteConfiguration.get_solo()
        return render(request, 'admin_panel/site_config.html', {
            'user': admin,
            'config': config,
        })

    def post(self, request):
        config = SiteConfiguration.get_solo()
        fields_text = [
            'site_name', 'tagline', 'hero_badge', 'hero_title_1', 'hero_title_2',
            'hero_subtitle', 'contact_email', 'contact_phone', 'whatsapp', 'address',
            'hours', 'facebook_url', 'instagram_url', 'twitter_url', 'youtube_url',
            'linkedin_url', 'android_apk_url', 'ios_store_url', 'meta_description',
            'google_analytics_id', 'copyright_text', 'maintenance_message',
        ]
        for f in fields_text:
            val = request.POST.get(f)
            if val is not None:
                setattr(config, f, val)

        config.maintenance_mode = bool(request.POST.get('maintenance_mode'))

        if request.FILES.get('logo'):
            config.logo = request.FILES['logo']
        if request.FILES.get('favicon'):
            config.favicon = request.FILES['favicon']
        if request.FILES.get('android_direct_apk'):
            config.android_direct_apk = request.FILES['android_direct_apk']

        config.save()
        messages.success(request, 'Configuration du site enregistrée.')
        return redirect('admin_site_config')
