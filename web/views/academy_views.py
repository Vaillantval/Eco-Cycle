import logging
from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from web.mixins import LoginRequiredMixin
from apps.academy.models import Course, Lesson, LessonVideo, Enrollment, Certificate

logger = logging.getLogger(__name__)


class AcademyListView(View):
    def get(self, request):
        level_filter = request.GET.get('level', '')
        courses = Course.objects.filter(is_published=True).prefetch_related('lessons').order_by('created_at')
        if level_filter:
            courses = courses.filter(level=level_filter)

        user_enrollments = {}
        if request.session.get('user_id'):
            from apps.accounts.models import User
            try:
                user = User.objects.get(id=request.session['user_id'])
                for e in Enrollment.objects.filter(user=user).select_related('course'):
                    user_enrollments[str(e.course_id)] = e
            except User.DoesNotExist:
                pass

        return render(request, 'academy/list.html', {
            'courses': courses,
            'level_filter': level_filter,
            'level_choices': Course.LEVEL_CHOICES,
            'user_enrollments': user_enrollments,
        })


class CourseDetailView(View):
    def get(self, request, slug):
        course = get_object_or_404(Course, slug=slug, is_published=True)
        lessons = course.lessons.all()
        enrollment = None
        completed_ids = set()

        if request.session.get('user_id'):
            from apps.accounts.models import User
            try:
                user = User.objects.get(id=request.session['user_id'])
                enrollment = Enrollment.objects.filter(user=user, course=course).first()
                if enrollment:
                    # Corriger en base si le cours est gratuit mais l'inscription est encore pending
                    if course.is_free and enrollment.payment_status == 'pending':
                        enrollment.payment_status = 'free'
                        enrollment.save(update_fields=['payment_status'])
                    completed_ids = set(str(l.id) for l in enrollment.completed_lessons.all())
            except User.DoesNotExist:
                pass

        lessons_list = list(lessons)
        continue_lesson = None
        if enrollment and not enrollment.is_completed:
            continue_lesson = next(
                (l for l in lessons_list if str(l.id) not in completed_ids),
                lessons_list[0] if lessons_list else None,
            )
        return render(request, 'academy/detail.html', {
            'course': course,
            'lessons': lessons_list,
            'enrollment': enrollment,
            'completed_ids': completed_ids,
            'total_lessons': len(lessons_list),
            'first_lesson': lessons_list[0] if lessons_list else None,
            'continue_lesson': continue_lesson,
        })


class EnrollCourseView(LoginRequiredMixin, View):
    def post(self, request, slug):
        user = self.get_current_user(request)
        course = get_object_or_404(Course, slug=slug, is_published=True)

        if not course.is_free:
            # Cours payant — rediriger vers le checkout
            return redirect('course_checkout', slug=slug)

        enrollment, created = Enrollment.objects.get_or_create(
            user=user, course=course,
            defaults={'payment_status': 'free'},
        )
        # Corriger une inscription "pending" si le cours est devenu gratuit
        if not created and enrollment.payment_status == 'pending':
            enrollment.payment_status = 'free'
            enrollment.save(update_fields=['payment_status'])
        if created:
            messages.success(request, f'Inscrit au cours « {course.title} » !')
            try:
                from apps.notifications.email_service import EmailService
                EmailService.send_free_enrollment_confirmation(enrollment)
            except Exception:
                pass
        else:
            messages.info(request, 'Vous êtes déjà inscrit à ce cours.')
        return redirect('course_detail', slug=slug)


class CompleteLessonView(LoginRequiredMixin, View):
    def post(self, request, slug, lesson_id):
        user = self.get_current_user(request)
        course = get_object_or_404(Course, slug=slug, is_published=True)
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
        enrollment = get_object_or_404(Enrollment, user=user, course=course)

        enrollment.completed_lessons.add(lesson)
        enrollment.update_progress()

        if enrollment.is_completed:
            cert, created = Certificate.objects.get_or_create(user=user, course=course)
            if created:
                from apps.notifications.tasks import notify_course_completed
                notify_course_completed.delay(str(user.id), str(course.id), str(cert.id))
            messages.success(request, f'Félicitations ! Cours « {course.title} » terminé ! Votre certificat est disponible.')
        return redirect('lesson_detail', slug=slug, lesson_id=lesson_id)


class LessonDetailView(LoginRequiredMixin, View):
    def get(self, request, slug, lesson_id):
        user = self.get_current_user(request)
        course = get_object_or_404(
            Course.objects.prefetch_related('lessons__videos'),
            slug=slug, is_published=True,
        )
        enrollment = get_object_or_404(
            Enrollment.objects.prefetch_related('completed_lessons'),
            user=user, course=course,
        )

        # Cours payant : bloquer si paiement non complété
        if not course.is_free and enrollment.payment_status != 'paid':
            messages.error(request, 'Finalisez le paiement pour accéder aux leçons.')
            return redirect('course_checkout', slug=slug)
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

        lessons = list(course.lessons.all())  # already prefetched, no extra query
        idx = next((i for i, l in enumerate(lessons) if str(l.id) == str(lesson.id)), 0)
        prev_lesson = lessons[idx - 1] if idx > 0 else None
        next_lesson = lessons[idx + 1] if idx < len(lessons) - 1 else None

        completed_ids = set(str(l.id) for l in enrollment.completed_lessons.all())  # prefetched
        is_done = str(lesson.id) in completed_ids
        videos = list(lesson.videos.all())  # prefetched via lessons__videos
        downloadable_videos = [v for v in videos if v.video_file and v.allow_download]

        return render(request, 'academy/lesson_detail.html', {
            'course': course,
            'lesson': lesson,
            'lessons': lessons,
            'videos': videos,
            'downloadable_videos': downloadable_videos,
            'enrollment': enrollment,
            'prev_lesson': prev_lesson,
            'next_lesson': next_lesson,
            'is_done': is_done,
            'completed_ids': completed_ids,
        })


# ─────────────────────────────────────────────────────────
#  Paiement des cours payants
# ─────────────────────────────────────────────────────────

class CourseCheckoutView(LoginRequiredMixin, View):
    """GET /academy/<slug>/pay/ — choisir le mode de paiement pour un cours payant."""

    def get(self, request, slug):
        from apps.payments.models import Transaction
        user   = self.get_current_user(request)
        course = get_object_or_404(Course, slug=slug, is_published=True)

        if course.is_free:
            return redirect('enroll_course', slug=slug)

        enrollment, _ = Enrollment.objects.get_or_create(
            user=user, course=course,
            defaults={'payment_status': 'pending'},
        )

        if enrollment.payment_status == 'paid':
            messages.info(request, 'Vous êtes déjà inscrit à ce cours.')
            return redirect('course_detail', slug=slug)

        if enrollment.payment_status == 'free':
            enrollment.payment_status = 'pending'
            enrollment.save(update_fields=['payment_status'])

        transaction, _ = Transaction.objects.get_or_create(
            enrollment=enrollment,
            defaults={'amount': course.price, 'currency': 'HTG'},
        )

        return render(request, 'payments/course_checkout.html', {
            'course':      course,
            'enrollment':  enrollment,
            'transaction': transaction,
        })


class CourseStripeInitView(LoginRequiredMixin, View):
    """POST /academy/<slug>/pay/stripe/init/ — crée le PaymentIntent pour un cours."""

    def post(self, request, slug):
        from apps.payments.models import Transaction
        from apps.payments.stripe_service import StripeService
        user   = self.get_current_user(request)
        course = get_object_or_404(Course, slug=slug, is_published=True)
        enrollment = get_object_or_404(Enrollment, user=user, course=course)

        if enrollment.payment_status == 'paid':
            return JsonResponse({'error': 'Déjà payé.'}, status=400)

        transaction, _ = Transaction.objects.get_or_create(
            enrollment=enrollment,
            defaults={'amount': course.price, 'currency': 'HTG'},
        )

        if transaction.status == 'completed':
            return JsonResponse({'error': 'Déjà payé.'}, status=400)

        existing_pi = transaction.meta_data.get('stripe_payment_intent_id')
        if existing_pi:
            svc    = StripeService()
            result = svc.retrieve_payment_intent(existing_pi)
            if result['success'] and result['status'] not in ('canceled', 'requires_payment_method'):
                return JsonResponse({
                    'success':            True,
                    'client_secret':      transaction.meta_data.get('stripe_client_secret'),
                    'transaction_number': transaction.transaction_number,
                })

        svc    = StripeService()
        result = svc.create_payment_intent(
            amount_htg=float(course.price),
            transaction_number=transaction.transaction_number,
            metadata={'enrollment_id': str(enrollment.id), 'course_slug': slug},
        )

        if not result['success']:
            return JsonResponse({'error': result.get('error', 'Erreur Stripe')}, status=502)

        transaction.meta_data['stripe_payment_intent_id'] = result['payment_intent_id']
        transaction.meta_data['stripe_client_secret']     = result['client_secret']
        transaction.payment_method = 'credit_card'
        transaction.save(update_fields=['meta_data', 'payment_method', 'updated_at'])

        return JsonResponse({
            'success':            True,
            'client_secret':      result['client_secret'],
            'transaction_number': transaction.transaction_number,
        })


class CourseStripeCheckoutView(LoginRequiredMixin, View):
    """GET /academy/<slug>/pay/stripe/ — page Stripe Elements pour un cours."""

    def get(self, request, slug):
        from django.conf import settings
        from apps.payments.models import Transaction
        user   = self.get_current_user(request)
        course = get_object_or_404(Course, slug=slug, is_published=True)
        enrollment = get_object_or_404(Enrollment, user=user, course=course)
        transaction = get_object_or_404(Transaction, enrollment=enrollment)

        return render(request, 'payments/course_stripe_checkout.html', {
            'course':           course,
            'enrollment':       enrollment,
            'transaction':      transaction,
            'stripe_public_key': settings.STRIPE['PUBLIC_KEY'],
        })


class CoursePlopPlopInitView(LoginRequiredMixin, View):
    """POST /academy/<slug>/pay/plopplop/ — initie PlopPlop pour un cours."""

    def post(self, request, slug):
        from apps.payments.models import Transaction
        from apps.payments.plopplop_service import PlopPlopService
        user   = self.get_current_user(request)
        course = get_object_or_404(Course, slug=slug, is_published=True)
        enrollment = get_object_or_404(Enrollment, user=user, course=course)
        method = request.POST.get('method', 'all')

        transaction, _ = Transaction.objects.get_or_create(
            enrollment=enrollment,
            defaults={'amount': course.price, 'currency': 'HTG'},
        )

        if transaction.status == 'completed':
            messages.info(request, 'Ce cours est déjà payé.')
            return redirect('course_detail', slug=slug)

        svc    = PlopPlopService()
        result = svc.create_payment(
            reference_id=transaction.transaction_number,
            montant=float(course.price),
            payment_method=method,
        )

        if not result['success']:
            messages.error(request, f'Erreur PlopPlop : {result.get("error", "Réessayez.")}')
            return redirect('course_checkout', slug=slug)

        transaction.payment_method = method if method != 'all' else 'moncash'
        transaction.meta_data['plopplop_url']            = result['url']
        transaction.meta_data['plopplop_transaction_id'] = result.get('transaction_id', '')
        transaction.save(update_fields=['payment_method', 'meta_data', 'updated_at'])

        return redirect(result['url'])
