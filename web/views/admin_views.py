from datetime import timedelta
from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils import timezone
from web.mixins import AdminRequiredMixin, LoginRequiredMixin
from apps.accounts.models import User
from apps.waste.models import WasteListing
from apps.collections.models import PickupRequest
from apps.marketplace.models import Order, Auction
from apps.blog.models import Post, BlogCategory
from apps.academy.models import Course, Lesson, LessonVideo, Enrollment, Certificate
from apps.core.models import ContactMessage, NewsletterSubscriber, SiteConfiguration, SliderItem


def _get_reading_duration_minutes(text: str) -> int:
    """Estimate reading time in minutes at 200 words/min. Returns 0 if no text."""
    words = len(text.split())
    return max(1, round(words / 200)) if words else 0


def _extract_pdf_text(file_obj):
    """Extract plain text from an uploaded PDF file object. Returns '' on failure."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_obj)
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ''
            if text.strip():
                pages.append(text.strip())
        return '\n\n'.join(pages)
    except Exception:
        return ''


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
        from django.core.paginator import Paginator
        user = self.get_current_user(request)
        status_filter = request.GET.get('status', '')
        search = request.GET.get('q', '').strip()
        listings = WasteListing.objects.select_related('user', 'category').order_by('-created_at')
        if status_filter:
            listings = listings.filter(status=status_filter)
        if search:
            listings = listings.filter(title__icontains=search) | listings.filter(user__email__icontains=search)
            listings = listings.distinct()
        paginator = Paginator(listings, 25)
        page = paginator.get_page(request.GET.get('page', 1))
        return render(request, 'admin_panel/listings.html', {
            'user': user,
            'listings': page,
            'status_filter': status_filter,
            'search': search,
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

            if not hasattr(listing, 'auction'):
                try:
                    starting_price = float(request.POST.get('starting_price') or 0)
                    if starting_price <= 0:
                        starting_price = float(listing.ai_estimated_value or 1000)

                    buy_now_raw = request.POST.get('buy_now_price', '').strip()
                    buy_now_price = float(buy_now_raw) if buy_now_raw else None

                    auction_type  = request.POST.get('auction_type', 'both')
                    duration_days = int(request.POST.get('duration_days') or 7)

                    Auction.objects.create(
                        listing=listing,
                        seller=listing.user,
                        auction_type=auction_type,
                        starting_price=starting_price,
                        current_price=starting_price,
                        buy_now_price=buy_now_price,
                        status='active',
                        starts_at=timezone.now(),
                        ends_at=timezone.now() + timedelta(days=duration_days),
                    )
                    from apps.notifications.tasks import notify_listing_approved
                    notify_listing_approved.delay(str(listing.id))
                    messages.success(request, f'Listing « {listing.title} » approuvé et publié sur le marketplace.')
                except Exception as e:
                    messages.warning(request, f'Listing approuvé mais erreur lors de la création de l\'enchère : {e}')
            else:
                messages.success(request, f'Listing « {listing.title} » approuvé (enchère déjà existante).')
        elif action == 'reject':
            reason = request.POST.get('rejection_reason', '').strip()
            listing.status = 'rejected'
            listing.reviewed_by = admin
            listing.reviewed_at = timezone.now()
            listing.rejection_reason = reason
            listing.save()
            from apps.notifications.tasks import notify_listing_rejected
            notify_listing_rejected.delay(str(listing.id))
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


class AdminAuctionsView(AdminRequiredMixin, View):
    def get(self, request):
        from django.core.paginator import Paginator
        user = self.get_current_user(request)
        status_filter = request.GET.get('status', '')
        search = request.GET.get('q', '').strip()
        auctions = Auction.objects.select_related(
            'listing', 'listing__category', 'seller', 'winner'
        ).order_by('-created_at')
        if status_filter:
            auctions = auctions.filter(status=status_filter)
        if search:
            auctions = auctions.filter(listing__title__icontains=search)
        paginator = Paginator(auctions, 20)
        page = paginator.get_page(request.GET.get('page', 1))
        return render(request, 'admin_panel/auctions.html', {
            'user': user,
            'auctions': page,
            'status_filter': status_filter,
            'search': search,
            'status_choices': Auction.STATUS_CHOICES,
            'count_active': Auction.objects.filter(status='active').count(),
            'count_sold':   Auction.objects.filter(status='sold').count(),
        })


class AdminCreateAuctionView(AdminRequiredMixin, View):
    def get(self, request):
        user = self.get_current_user(request)
        # Only approved listings without an existing auction
        listings = (
            WasteListing.objects
            .filter(status='approved')
            .exclude(auction__isnull=False)
            .select_related('user', 'category')
            .order_by('-created_at')
        )
        return render(request, 'admin_panel/auction_form.html', {
            'user': user,
            'listings': listings,
        })

    def post(self, request):
        from datetime import timedelta
        try:
            listing_id   = request.POST.get('listing_id')
            listing      = get_object_or_404(WasteListing, pk=listing_id, status='approved')

            if hasattr(listing, 'auction'):
                messages.error(request, 'Ce listing a déjà une enchère.')
                return redirect('admin_create_auction')

            starting_price = float(request.POST.get('starting_price') or 0)
            if starting_price <= 0:
                raise ValueError('Le prix de départ doit être supérieur à 0.')

            buy_now_raw   = request.POST.get('buy_now_price', '').strip()
            reserve_raw   = request.POST.get('reserve_price', '').strip()
            auction_type  = request.POST.get('auction_type', 'both')

            # Dates : soit starts_at/ends_at saisis, soit durée en jours
            starts_at_raw = request.POST.get('starts_at', '').strip()
            ends_at_raw   = request.POST.get('ends_at', '').strip()
            duration_days = int(request.POST.get('duration_days') or 7)

            now = timezone.now()
            if starts_at_raw:
                from django.utils.dateparse import parse_datetime
                starts_at = timezone.make_aware(
                    parse_datetime(starts_at_raw),
                    timezone.get_current_timezone()
                ) if not starts_at_raw.endswith('Z') else parse_datetime(starts_at_raw)
            else:
                starts_at = now

            if ends_at_raw:
                from django.utils.dateparse import parse_datetime
                ends_at = timezone.make_aware(
                    parse_datetime(ends_at_raw),
                    timezone.get_current_timezone()
                ) if not ends_at_raw.endswith('Z') else parse_datetime(ends_at_raw)
            else:
                ends_at = starts_at + timedelta(days=duration_days)

            auction = Auction.objects.create(
                listing=listing,
                seller=listing.user,
                auction_type=auction_type,
                starting_price=starting_price,
                current_price=starting_price,
                buy_now_price=float(buy_now_raw) if buy_now_raw else None,
                reserve_price=float(reserve_raw) if reserve_raw else None,
                status='active',
                starts_at=starts_at,
                ends_at=ends_at,
            )
            listing.status = 'approved'
            listing.save(update_fields=['status', 'updated_at'])
            messages.success(request, f'Enchère créée pour « {listing.title} ».')
            return redirect('admin_auction_detail', pk=auction.pk)

        except ValueError as e:
            messages.error(request, str(e))
            return redirect('admin_create_auction')
        except Exception as e:
            messages.error(request, f'Erreur : {e}')
            return redirect('admin_create_auction')


class AdminAuctionDetailView(AdminRequiredMixin, View):
    def get(self, request, pk):
        user = self.get_current_user(request)
        auction = get_object_or_404(
            Auction.objects.select_related('listing', 'listing__category', 'seller', 'winner'),
            pk=pk,
        )
        bids  = auction.bids.select_related('bidder').order_by('-amount')
        order = getattr(auction, 'order', None)
        return render(request, 'admin_panel/auction_detail.html', {
            'user': user,
            'auction': auction,
            'bids': bids,
            'order': order,
        })

    def post(self, request, pk):
        auction = get_object_or_404(Auction, pk=pk)
        action  = request.POST.get('action')
        if action == 'cancel' and auction.status == 'active':
            auction.status = 'cancelled'
            auction.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Enchère annulée.')
        elif action == 'close' and auction.status == 'active':
            auction.status = 'closed'
            auction.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Enchère clôturée manuellement.')
        return redirect('admin_auction_detail', pk=pk)


class AdminOrdersView(AdminRequiredMixin, View):
    def get(self, request):
        from django.core.paginator import Paginator
        user = self.get_current_user(request)
        status_filter = request.GET.get('status', '')
        search = request.GET.get('q', '').strip()
        orders = Order.objects.select_related('buyer', 'seller', 'auction__listing').order_by('-created_at')
        if status_filter:
            orders = orders.filter(status=status_filter)
        if search:
            orders = orders.filter(buyer__email__icontains=search) | orders.filter(auction__listing__title__icontains=search)
            orders = orders.distinct()
        paginator = Paginator(orders, 25)
        page = paginator.get_page(request.GET.get('page', 1))
        return render(request, 'admin_panel/orders.html', {
            'user': user,
            'orders': page,
            'status_filter': status_filter,
            'search': search,
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
        order  = get_object_or_404(Order, pk=pk)
        action = request.POST.get('action', 'change_status')

        if action == 'save_notes':
            order.notes = request.POST.get('notes', '').strip()
            order.save(update_fields=['notes', 'updated_at'])
            messages.success(request, 'Notes sauvegardées.')
        else:
            new_status = request.POST.get('new_status')
            valid = [s for s, _ in Order.STATUS_CHOICES]
            if new_status in valid:
                order.status = new_status
                if new_status == 'completed':
                    order.completed_at = timezone.now()
                order.save()
                messages.success(request, f'Commande mise à jour : {new_status}.')
        return redirect('admin_order_detail', pk=pk)


# ══════════════════════════════════════════════════════
#  BLOG
# ══════════════════════════════════════════════════════

class AdminBlogView(AdminRequiredMixin, View):
    def get(self, request):
        admin = self.get_current_user(request)
        status_filter   = request.GET.get('status', '')
        category_filter = request.GET.get('category', '')
        search          = request.GET.get('q', '')
        posts = Post.objects.select_related('author', 'category').order_by('-created_at')
        if status_filter:
            posts = posts.filter(status=status_filter)
        if category_filter:
            posts = posts.filter(category_id=category_filter)
        if search:
            posts = posts.filter(title__icontains=search) | posts.filter(excerpt__icontains=search)
        return render(request, 'admin_panel/blog.html', {
            'user': admin,
            'posts': posts,
            'status_filter': status_filter,
            'category_filter': category_filter,
            'search': search,
            'categories': BlogCategory.objects.order_by('name'),
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


class AdminBlogCreateView(AdminRequiredMixin, View):
    def get(self, request):
        admin = self.get_current_user(request)
        return render(request, 'admin_panel/blog_form.html', {
            'user': admin,
            'categories': BlogCategory.objects.order_by('name'),
            'post': None,
            'data': {},
        })

    def post(self, request):
        admin = self.get_current_user(request)
        title   = request.POST.get('title', '').strip()
        excerpt = request.POST.get('excerpt', '').strip()
        content = request.POST.get('content', '').strip()
        if not title or not excerpt or not content:
            messages.error(request, 'Titre, extrait et contenu sont obligatoires.')
            return render(request, 'admin_panel/blog_form.html', {
                'user': admin,
                'categories': BlogCategory.objects.order_by('name'),
                'post': None,
                'data': request.POST,
            })
        post = Post(
            author=admin,
            title=title,
            excerpt=excerpt,
            content=content,
            category_id=request.POST.get('category') or None,
            read_time_minutes=request.POST.get('read_time_minutes') or 5,
            status=request.POST.get('status', 'draft'),
        )
        if request.FILES.get('cover_image'):
            post.cover_image = request.FILES['cover_image']
        if post.status == 'published':
            post.published_at = timezone.now()
        post.save()
        messages.success(request, f'Article « {post.title} » créé.')
        return redirect('admin_blog_edit', pk=post.id)


class AdminBlogEditView(AdminRequiredMixin, View):
    def get(self, request, pk):
        admin = self.get_current_user(request)
        post = get_object_or_404(Post, pk=pk)
        return render(request, 'admin_panel/blog_form.html', {
            'user': admin,
            'post': post,
            'categories': BlogCategory.objects.order_by('name'),
            'data': {},
        })

    def post(self, request, pk):
        admin = self.get_current_user(request)
        post = get_object_or_404(Post, pk=pk)
        title   = request.POST.get('title', '').strip()
        excerpt = request.POST.get('excerpt', '').strip()
        content = request.POST.get('content', '').strip()
        if not title or not excerpt or not content:
            messages.error(request, 'Titre, extrait et contenu sont obligatoires.')
            return render(request, 'admin_panel/blog_form.html', {
                'user': admin,
                'post': post,
                'categories': BlogCategory.objects.order_by('name'),
            })
        old_status = post.status
        post.title            = title
        post.excerpt          = excerpt
        post.content          = content
        post.category_id      = request.POST.get('category') or None
        post.read_time_minutes = request.POST.get('read_time_minutes') or 5
        post.status           = request.POST.get('status', 'draft')
        if request.FILES.get('cover_image'):
            post.cover_image = request.FILES['cover_image']
        if post.status == 'published' and old_status != 'published':
            post.published_at = timezone.now()
        post.save()
        messages.success(request, f'Article « {post.title} » mis à jour.')
        return redirect('admin_blog_edit', pk=post.id)


class AdminBlogCategoriesView(AdminRequiredMixin, View):
    def get(self, request):
        admin = self.get_current_user(request)
        return render(request, 'admin_panel/blog_categories.html', {
            'user': admin,
            'categories': BlogCategory.objects.order_by('name'),
        })

    def post(self, request):
        action = request.POST.get('action')
        if action == 'create':
            name = request.POST.get('name', '').strip()
            if name:
                from django.utils.text import slugify
                BlogCategory.objects.get_or_create(
                    slug=slugify(name), defaults={'name': name}
                )
                messages.success(request, f'Catégorie « {name} » créée.')
            else:
                messages.error(request, 'Le nom est requis.')
        elif action == 'edit':
            cat_id = request.POST.get('cat_id')
            cat = get_object_or_404(BlogCategory, pk=cat_id)
            name = request.POST.get('name', '').strip()
            if name:
                cat.name = name
                cat.save()
                messages.success(request, 'Catégorie mise à jour.')
        elif action == 'delete':
            cat_id = request.POST.get('cat_id')
            cat = get_object_or_404(BlogCategory, pk=cat_id)
            cat.delete()
            messages.warning(request, 'Catégorie supprimée.')
        return redirect('admin_blog_categories')


# ══════════════════════════════════════════════════════
#  ACADEMY
# ══════════════════════════════════════════════════════

class AdminAcademyView(AdminRequiredMixin, View):
    def get(self, request):
        admin = self.get_current_user(request)
        level_filter     = request.GET.get('level', '')
        published_filter = request.GET.get('published', '')
        free_filter      = request.GET.get('free', '')
        search           = request.GET.get('q', '')
        courses = Course.objects.prefetch_related('lessons', 'enrollments').order_by('-created_at')
        if level_filter:
            courses = courses.filter(level=level_filter)
        if published_filter == '1':
            courses = courses.filter(is_published=True)
        elif published_filter == '0':
            courses = courses.filter(is_published=False)
        if free_filter == '1':
            courses = courses.filter(price=0)
        elif free_filter == '0':
            courses = courses.filter(price__gt=0)
        if search:
            courses = courses.filter(title__icontains=search)
        return render(request, 'admin_panel/academy.html', {
            'user': admin,
            'courses': courses,
            'level_filter': level_filter,
            'published_filter': published_filter,
            'free_filter': free_filter,
            'search': search,
            'level_choices': Course.LEVEL_CHOICES,
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
        elif action == 'delete':
            title = course.title
            course.delete()
            messages.warning(request, f'Cours « {title} » supprimé.')
        return redirect('admin_academy')


class AdminAcademyCourseCreateView(AdminRequiredMixin, View):
    def get(self, request):
        admin = self.get_current_user(request)
        return render(request, 'admin_panel/academy_course_form.html', {
            'user': admin,
            'course': None,
            'level_choices': Course.LEVEL_CHOICES,
        })

    def post(self, request):
        admin = self.get_current_user(request)
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        if not title or not description:
            messages.error(request, 'Titre et description sont obligatoires.')
            return render(request, 'admin_panel/academy_course_form.html', {
                'user': admin, 'course': None, 'level_choices': Course.LEVEL_CHOICES,
            })
        try:
            price_val = abs(float(request.POST.get('price', 0) or 0))
        except (ValueError, TypeError):
            price_val = 0
        try:
            delay_val = max(0, int(request.POST.get('auto_advance_delay', 0) or 0))
        except (ValueError, TypeError):
            delay_val = 0
        course = Course(
            title=title,
            description=description,
            level=request.POST.get('level', 'beginner'),
            is_published=bool(request.POST.get('is_published')),
            price=price_val,
            auto_advance_delay=delay_val,
        )
        if request.FILES.get('thumbnail'):
            course.thumbnail = request.FILES['thumbnail']
        course.save()
        messages.success(request, f'Cours « {course.title} » créé.')
        return redirect('admin_academy_course_detail', pk=course.id)


class AdminAcademyCourseDetailView(AdminRequiredMixin, View):
    """Détail cours + gestion des leçons."""
    def get(self, request, pk):
        admin = self.get_current_user(request)
        course = get_object_or_404(Course, pk=pk)
        lessons = course.lessons.order_by('order')
        enrollments = Enrollment.objects.filter(course=course).select_related('user').order_by('-enrolled_at')[:20]
        return render(request, 'admin_panel/academy_course_detail.html', {
            'user': admin,
            'course': course,
            'lessons': lessons,
            'enrollments': enrollments,
            'level_choices': Course.LEVEL_CHOICES,
        })

    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        action = request.POST.get('action')

        if action == 'update_course':
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            if not title or not description:
                messages.error(request, 'Titre et description requis.')
                return redirect('admin_academy_course_detail', pk=pk)
            try:
                price_val = abs(float(request.POST.get('price', 0) or 0))
            except (ValueError, TypeError):
                price_val = 0
            try:
                delay_val = max(0, int(request.POST.get('auto_advance_delay', 0) or 0))
            except (ValueError, TypeError):
                delay_val = 0
            course.title               = title
            course.description         = description
            course.level               = request.POST.get('level', 'beginner')
            course.is_published        = bool(request.POST.get('is_published'))
            course.price               = price_val
            course.auto_advance_delay  = delay_val
            if request.FILES.get('thumbnail'):
                course.thumbnail = request.FILES['thumbnail']
            course.save()
            messages.success(request, 'Cours mis à jour.')

        elif action == 'delete_lesson':
            lesson_id = request.POST.get('lesson_id')
            lesson = get_object_or_404(Lesson, pk=lesson_id, course=course)
            title = lesson.title
            lesson.delete()
            messages.warning(request, f'Leçon « {title} » supprimée.')

        elif action == 'toggle_publish':
            course.is_published = not course.is_published
            course.save()
            state = 'publié' if course.is_published else 'dépublié'
            messages.success(request, f'Cours {state}.')

        return redirect('admin_academy_course_detail', pk=pk)


class AdminAcademyLessonCreateView(AdminRequiredMixin, View):
    def get(self, request, course_pk):
        admin  = self.get_current_user(request)
        course = get_object_or_404(Course, pk=course_pk)
        next_order = course.lessons.count() + 1
        return render(request, 'admin_panel/academy_lesson_form.html', {
            'user': admin,
            'course': course,
            'lesson': None,
            'next_order': next_order,
        })

    def post(self, request, course_pk):
        course = get_object_or_404(Course, pk=course_pk)
        title  = request.POST.get('title', '').strip()
        if not title:
            messages.error(request, 'Le titre est obligatoire.')
            return redirect('admin_academy_lesson_create', course_pk=course_pk)
        content          = request.POST.get('content', '')
        pdf_file         = request.FILES.get('pdf_file')
        pdf_display_mode = request.POST.get('pdf_display_mode', 'extract')
        if pdf_file and pdf_display_mode == 'extract':
            extracted = _extract_pdf_text(pdf_file)
            if extracted:
                content = extracted
                messages.info(request, f'Texte extrait du PDF ({len(extracted)} caractères).')
            else:
                messages.warning(request, 'PDF uploadé mais aucun texte n\'a pu être extrait.')
            pdf_file.seek(0)
        elif pdf_file:
            pdf_file.seek(0)
        lesson = Lesson.objects.create(
            course             = course,
            title              = title,
            content            = content,
            pdf_file           = pdf_file if pdf_file else None,
            pdf_display_mode   = pdf_display_mode,
            pdf_allow_download = request.POST.get('pdf_allow_download') == '1',
            order              = request.POST.get('order') or course.lessons.count(),
        )
        # Ajouter la première vidéo si fournie
        video_file = request.FILES.get('video_file')
        video_url  = request.POST.get('video_url', '').strip()
        if video_file or video_url:
            duration = int(request.POST.get('video_duration') or 0)
            if not duration and video_url:
                duration = _get_youtube_duration_minutes(video_url)
            LessonVideo.objects.create(
                lesson           = lesson,
                title            = request.POST.get('video_title', '').strip(),
                video_file       = video_file,
                video_url        = video_url,
                allow_download   = request.POST.get('video_allow_download') == '1',
                order            = 1,
                duration_minutes = duration,
            )
        messages.success(request, f'Leçon « {lesson.title} » créée.')
        return redirect('admin_academy_lesson_edit', course_pk=course_pk, lesson_pk=lesson.pk)


class AdminAcademyLessonEditView(AdminRequiredMixin, View):
    def _render(self, request, course, lesson):
        return render(request, 'admin_panel/academy_lesson_form.html', {
            'user': self.get_current_user(request),
            'course': course,
            'lesson': lesson,
            'videos': lesson.videos.all(),
        })

    def get(self, request, course_pk, lesson_pk):
        course = get_object_or_404(Course, pk=course_pk)
        lesson = get_object_or_404(Lesson, pk=lesson_pk, course=course)
        return self._render(request, course, lesson)

    def post(self, request, course_pk, lesson_pk):
        course = get_object_or_404(Course, pk=course_pk)
        lesson = get_object_or_404(Lesson, pk=lesson_pk, course=course)
        action = request.POST.get('action', 'save_lesson')

        if action == 'add_video':
            video_file = request.FILES.get('video_file')
            video_url  = request.POST.get('video_url', '').strip()
            if video_file or video_url:
                duration = int(request.POST.get('video_duration') or 0)
                if not duration and video_url:
                    duration = _get_youtube_duration_minutes(video_url)
                LessonVideo.objects.create(
                    lesson           = lesson,
                    title            = request.POST.get('video_title', '').strip(),
                    video_file       = video_file,
                    video_url        = video_url,
                    allow_download   = request.POST.get('video_allow_download') == '1',
                    order            = request.POST.get('video_order') or lesson.videos.count() + 1,
                    duration_minutes = duration,
                )
                messages.success(request, 'Vidéo ajoutée.')
            else:
                messages.error(request, 'Fichier ou URL requis.')
            return redirect('admin_academy_lesson_edit', course_pk=course_pk, lesson_pk=lesson_pk)

        if action == 'update_video':
            video = get_object_or_404(LessonVideo, pk=request.POST.get('video_id'), lesson=lesson)
            video.title          = request.POST.get('video_title', '').strip()
            video.order          = int(request.POST.get('video_order') or video.order)
            video.allow_download = request.POST.get('video_allow_download') == '1'
            source = request.POST.get('video_source', 'url')
            if source == 'file':
                new_file = request.FILES.get('video_file')
                if new_file:
                    video.video_file = new_file
                    video.video_url  = ''
            else:
                url_val = request.POST.get('video_url', '').strip()
                video.video_url = url_val
                if url_val and video.video_file:
                    video.video_file = None
            duration = int(request.POST.get('video_duration') or 0)
            if not duration and video.video_url:
                duration = _get_youtube_duration_minutes(video.video_url)
            video.duration_minutes = duration
            video.save()
            messages.success(request, 'Vidéo mise à jour.')
            return redirect('admin_academy_lesson_edit', course_pk=course_pk, lesson_pk=lesson_pk)

        if action == 'delete_video':
            video = get_object_or_404(LessonVideo, pk=request.POST.get('video_id'), lesson=lesson)
            video.delete()
            messages.success(request, 'Vidéo supprimée.')
            return redirect('admin_academy_lesson_edit', course_pk=course_pk, lesson_pk=lesson_pk)

        if action == 'toggle_video_download':
            video = get_object_or_404(LessonVideo, pk=request.POST.get('video_id'), lesson=lesson)
            video.allow_download = not video.allow_download
            video.save(update_fields=['allow_download'])
            return redirect('admin_academy_lesson_edit', course_pk=course_pk, lesson_pk=lesson_pk)

        # default: save_lesson
        lesson.title              = request.POST.get('title', '').strip() or lesson.title
        lesson.order              = request.POST.get('order') or lesson.order
        lesson.pdf_allow_download = request.POST.get('pdf_allow_download') == '1'
        lesson.pdf_display_mode   = request.POST.get('pdf_display_mode', lesson.pdf_display_mode)
        pdf_file                  = request.FILES.get('pdf_file')
        replace_content           = request.POST.get('replace_content') == '1'
        pdf_reading_duration      = 0
        if pdf_file:
            if lesson.pdf_display_mode == 'extract':
                extracted = _extract_pdf_text(pdf_file)
                if extracted:
                    pdf_reading_duration = _get_reading_duration_minutes(extracted)
                    if replace_content or not lesson.content.strip():
                        lesson.content = extracted
                        messages.info(request, f'Contenu remplacé par le texte du PDF ({len(extracted)} caractères).')
                    else:
                        lesson.content = lesson.content.rstrip() + '\n\n' + extracted
                        messages.info(request, f'Texte du PDF ajouté à la fin ({len(extracted)} caractères).')
                else:
                    messages.warning(request, 'PDF uploadé mais aucun texte n\'a pu être extrait.')
            else:
                messages.info(request, 'PDF uploadé — affiché en visionneuse pour l\'utilisateur.')
            pdf_file.seek(0)
            lesson.pdf_file = pdf_file
        else:
            if lesson.pdf_display_mode == 'extract':
                lesson.content = request.POST.get('content', '')
        # Durée manuelle (PDF) — ignorée si la leçon a des vidéos (sync_duration fait foi)
        if not lesson.videos.exists():
            manual_duration = int(request.POST.get('lesson_duration') or 0)
            if manual_duration:
                # L'admin a saisi une valeur non nulle → elle prime
                lesson.duration_minutes = manual_duration
            elif pdf_reading_duration:
                # Pas de saisie manuelle, mais on vient d'extraire un PDF → durée auto
                lesson.duration_minutes = pdf_reading_duration
            # Si les deux sont 0 → on ne touche pas à la durée existante
        lesson.save()
        if pdf_reading_duration and not int(request.POST.get('lesson_duration') or 0):
            messages.info(request, f'Durée de lecture estimée automatiquement : {pdf_reading_duration} min.')
        messages.success(request, f'Leçon « {lesson.title} » mise à jour.')
        return redirect('admin_academy_lesson_edit', course_pk=course_pk, lesson_pk=lesson_pk)


class AdminAcademyEnrollmentsView(AdminRequiredMixin, View):
    def _context(self, request, admin):
        course_filter    = request.GET.get('course', '')
        completed_filter = request.GET.get('completed', '')
        enrollments = Enrollment.objects.select_related('user', 'course').order_by('-enrolled_at')
        if course_filter:
            enrollments = enrollments.filter(course_id=course_filter)
        if completed_filter == '1':
            enrollments = enrollments.filter(is_completed=True)
        elif completed_filter == '0':
            enrollments = enrollments.filter(is_completed=False)
        return {
            'user': admin,
            'enrollments': enrollments,
            'course_filter': course_filter,
            'completed_filter': completed_filter,
            'courses': Course.objects.order_by('title'),
            'users': User.objects.filter(is_active=True).order_by('email'),
        }

    def get(self, request):
        admin = self.get_current_user(request)
        return render(request, 'admin_panel/academy_enrollments.html', self._context(request, admin))

    def post(self, request):
        action = request.POST.get('action')
        if action == 'create':
            user_id   = request.POST.get('user_id')
            course_id = request.POST.get('course_id')
            if user_id and course_id:
                user   = get_object_or_404(User, pk=user_id)
                course = get_object_or_404(Course, pk=course_id)
                _, created = Enrollment.objects.get_or_create(user=user, course=course)
                if created:
                    messages.success(request, f'{user.email} inscrit à « {course.title} ».')
                else:
                    messages.warning(request, 'Cette inscription existe déjà.')
            else:
                messages.error(request, 'Utilisateur et cours requis.')
        elif action == 'delete':
            enr_id = request.POST.get('enr_id')
            Enrollment.objects.filter(pk=enr_id).delete()
            messages.success(request, 'Inscription supprimée.')
        return redirect('admin_academy_enrollments')


class AdminAcademyCertificatesView(AdminRequiredMixin, View):
    def get(self, request):
        admin = self.get_current_user(request)
        search = request.GET.get('q', '')
        certs = Certificate.objects.select_related('user', 'course').order_by('-issued_at')
        if search:
            certs = certs.filter(user__email__icontains=search) | certs.filter(course__title__icontains=search)
        return render(request, 'admin_panel/academy_certificates.html', {
            'user': admin,
            'certificates': certs,
            'search': search,
            'courses': Course.objects.filter(is_published=True).order_by('title'),
            'users': User.objects.filter(is_active=True).order_by('email'),
        })

    def post(self, request):
        action = request.POST.get('action')
        if action == 'create':
            user_id  = request.POST.get('user_id')
            course_id = request.POST.get('course_id')
            if user_id and course_id:
                user   = get_object_or_404(User, pk=user_id)
                course = get_object_or_404(Course, pk=course_id)
                _, created = Certificate.objects.get_or_create(user=user, course=course)
                if created:
                    messages.success(request, f'Certificat créé pour {user.email} — {course.title}.')
                else:
                    messages.warning(request, 'Ce certificat existe déjà.')
            else:
                messages.error(request, 'Utilisateur et cours requis.')
        elif action == 'delete':
            cert_id = request.POST.get('cert_id')
            Certificate.objects.filter(pk=cert_id).delete()
            messages.success(request, 'Certificat supprimé.')
        return redirect('admin_academy_certificates')


class AdminSlidersView(AdminRequiredMixin, View):
    def get(self, request):
        admin = self.get_current_user(request)
        return render(request, 'admin_panel/sliders.html', {
            'user': admin,
            'slides': SliderItem.objects.order_by('ordre'),
        })

    def post(self, request):
        action = request.POST.get('action')

        if action == 'create':
            slide = SliderItem(
                title    = request.POST.get('title', '').strip(),
                subtitle = request.POST.get('subtitle', ''),
                btn_text = request.POST.get('btn_text', ''),
                btn_url  = request.POST.get('btn_url', ''),
                ordre    = request.POST.get('ordre') or 0,
                is_active = bool(request.POST.get('is_active')),
            )
            if request.FILES.get('image'):
                slide.image = request.FILES['image']
            slide.save()
            messages.success(request, f'Slide « {slide.title} » créée.')

        elif action == 'update':
            slide_id = request.POST.get('slide_id')
            slide = get_object_or_404(SliderItem, pk=slide_id)
            slide.title    = request.POST.get('title', slide.title).strip()
            slide.subtitle = request.POST.get('subtitle', slide.subtitle)
            slide.btn_text = request.POST.get('btn_text', slide.btn_text)
            slide.btn_url  = request.POST.get('btn_url', slide.btn_url)
            slide.ordre    = request.POST.get('ordre') or slide.ordre
            slide.is_active = bool(request.POST.get('is_active'))
            if request.FILES.get('image'):
                slide.image = request.FILES['image']
            slide.save()
            messages.success(request, f'Slide « {slide.title} » mise à jour.')

        elif action == 'toggle':
            slide_id = request.POST.get('slide_id')
            slide = get_object_or_404(SliderItem, pk=slide_id)
            slide.is_active = not slide.is_active
            slide.save()

        elif action == 'delete':
            slide_id = request.POST.get('slide_id')
            SliderItem.objects.filter(pk=slide_id).delete()
            messages.success(request, 'Slide supprimée.')

        return redirect('admin_sliders')


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
            'linkedin_url', 'meta_description',
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
        if request.FILES.get('ios_direct_ipa'):
            config.ios_direct_ipa = request.FILES['ios_direct_ipa']

        config.save()
        messages.success(request, 'Configuration du site enregistrée.')
        return redirect('admin_site_config')


# ── PDF certificate generation ─────────────────────────────────────────────

def _build_certificate_pdf(certificate):
    """Return a BytesIO containing the PDF for the given Certificate object."""
    import io
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    W, H = landscape(A4)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))

    # Fond vert foncé sur les bords
    c.setFillColorRGB(0.05, 0.17, 0.13)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Cadre blanc central
    margin = 1.8 * cm
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(margin, margin, W - 2 * margin, H - 2 * margin, 12, fill=1, stroke=0)

    # Bordure décorative intérieure
    c.setStrokeColorRGB(0.05, 0.48, 0.27)
    c.setLineWidth(2.5)
    inner = 0.5 * cm
    c.roundRect(margin + inner, margin + inner,
                W - 2 * (margin + inner), H - 2 * (margin + inner),
                8, fill=0, stroke=1)

    # Logo texte
    c.setFillColorRGB(0.05, 0.48, 0.27)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(W / 2, H - 3.2 * cm, "EcoCycle Haiti")

    # Titre certificat
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(W / 2, H - 5.2 * cm, "Certificat de Réussite")

    # Ligne décorative
    c.setStrokeColorRGB(0.05, 0.48, 0.27)
    c.setLineWidth(1.5)
    c.line(W / 2 - 7 * cm, H - 5.7 * cm, W / 2 + 7 * cm, H - 5.7 * cm)

    # Texte principal
    c.setFont("Helvetica", 14)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawCentredString(W / 2, H - 7 * cm, "Ce certificat est décerné à")

    # Nom de l'utilisateur
    c.setFont("Helvetica-Bold", 26)
    c.setFillColorRGB(0.05, 0.17, 0.13)
    c.drawCentredString(W / 2, H - 8.5 * cm, certificate.user.full_name)

    # Ligne sous le nom
    c.setStrokeColorRGB(0.3, 0.3, 0.3)
    c.setLineWidth(0.8)
    c.line(W / 2 - 8 * cm, H - 8.9 * cm, W / 2 + 8 * cm, H - 8.9 * cm)

    # Pour avoir complété
    c.setFont("Helvetica", 13)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawCentredString(W / 2, H - 10 * cm, "pour avoir complété avec succès le cours")

    # Titre du cours
    c.setFont("Helvetica-Bold", 18)
    c.setFillColorRGB(0.05, 0.48, 0.27)
    course_title = certificate.course.title
    if len(course_title) > 55:
        course_title = course_title[:52] + "..."
    c.drawCentredString(W / 2, H - 11.3 * cm, course_title)

    # Date d'émission
    from django.utils.formats import date_format
    issued = date_format(certificate.issued_at, "d F Y")
    c.setFont("Helvetica", 11)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawCentredString(W / 2, H - 12.8 * cm, f"Délivré le {issued}")

    # ID unique
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.7, 0.7, 0.7)
    c.drawCentredString(W / 2, margin + 1 * cm, f"ID : {certificate.id}")

    # Sceau EcoCycle (cercle décoratif)
    c.setFillColorRGB(0.05, 0.48, 0.27)
    c.circle(W / 2, margin + 3 * cm, 0.8 * cm, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(W / 2, margin + 2.65 * cm, "♻")

    c.save()
    buf.seek(0)
    return buf


class CertificatePDFView(LoginRequiredMixin, View):
    """Accessible par l'utilisateur pour ses propres certificats."""
    def get(self, request, cert_id):
        user = self.get_current_user(request)
        cert = get_object_or_404(Certificate, pk=cert_id, user=user)
        buf = _build_certificate_pdf(cert)
        filename = f"certificat-{cert.course.title[:30].replace(' ', '-')}.pdf"
        response = HttpResponse(buf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class AdminCertificatePDFView(AdminRequiredMixin, View):
    """Accessible par l'admin pour n'importe quel certificat."""
    def get(self, request, cert_id):
        cert = get_object_or_404(Certificate, pk=cert_id)
        buf = _build_certificate_pdf(cert)
        filename = f"certificat-{cert.user.full_name[:20].replace(' ', '-')}-{cert.course.title[:20].replace(' ', '-')}.pdf"
        response = HttpResponse(buf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


def _get_youtube_duration_minutes(url: str) -> int:
    """Return duration in minutes for a YouTube URL using yt-dlp. Returns 0 on failure."""
    import re
    if not re.search(r'(?:youtube\.com|youtu\.be)', url):
        return 0
    try:
        import yt_dlp
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'extract_flat': False,
            'no_warnings': True,
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            seconds = info.get('duration') or 0
            return max(1, round(seconds / 60)) if seconds else 0
    except Exception:
        return 0


class AdminVideoDurationView(AdminRequiredMixin, View):
    """AJAX endpoint: POST {"url": "..."} → {"duration_minutes": N}"""
    def post(self, request):
        import json
        try:
            body = json.loads(request.body)
            url = body.get('url', '').strip()
        except Exception:
            return JsonResponse({'error': 'invalid json'}, status=400)
        if not url:
            return JsonResponse({'duration_minutes': 0})
        minutes = _get_youtube_duration_minutes(url)
        return JsonResponse({'duration_minutes': minutes})
