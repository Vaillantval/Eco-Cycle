import logging
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from .models import Course, Lesson, LessonVideo, Enrollment, Certificate
from .serializers import (
    CourseListSerializer, CourseDetailSerializer,
    EnrollmentSerializer, CertificateSerializer,
    AdminCourseSerializer, AdminLessonSerializer, AdminLessonVideoSerializer,
)
from apps.accounts.permissions import IsAdmin

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════
#  Endpoints publics / utilisateur
# ═════════════════════════════════════════════════════════

class CourseListView(generics.ListAPIView):
    """GET /api/academy/courses/"""
    serializer_class = CourseListSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Course.objects.filter(is_published=True)
    filterset_fields = ['level']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'duration_minutes']


class CourseDetailView(generics.RetrieveAPIView):
    """GET /api/academy/courses/<slug>/"""
    serializer_class = CourseDetailSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Course.objects.filter(is_published=True).prefetch_related('lessons__videos')
    lookup_field = 'slug'


class EnrollView(APIView):
    """POST /api/academy/courses/<slug>/enroll/"""
    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug, is_published=True)
        enrollment, created = Enrollment.objects.get_or_create(
            user=request.user, course=course,
            defaults={'payment_status': 'free' if course.is_free else 'pending'},
        )
        if created and course.is_free:
            try:
                from apps.notifications.email_service import EmailService
                EmailService.send_free_enrollment_confirmation(enrollment)
            except Exception:
                pass
        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class CompleteLessonView(APIView):
    """POST /api/academy/lessons/<id>/complete/"""
    def post(self, request, pk):
        lesson = get_object_or_404(Lesson, pk=pk)
        enrollment = get_object_or_404(
            Enrollment, user=request.user, course=lesson.course
        )
        enrollment.completed_lessons.add(lesson)
        enrollment.update_progress()

        if enrollment.is_completed:
            cert, created = Certificate.objects.get_or_create(
                user=request.user, course=lesson.course
            )
            if created:
                try:
                    from apps.notifications.tasks import notify_course_completed
                    notify_course_completed.delay(
                        str(request.user.id), str(lesson.course.id), str(cert.id)
                    )
                except Exception:
                    pass

        return Response(EnrollmentSerializer(enrollment).data)


class MyEnrollmentsView(generics.ListAPIView):
    """GET /api/academy/my-enrollments/"""
    serializer_class = EnrollmentSerializer

    def get_queryset(self):
        return Enrollment.objects.filter(
            user=self.request.user
        ).select_related('course').prefetch_related('completed_lessons')


class MyCertificatesView(generics.ListAPIView):
    """GET /api/academy/my-certificates/"""
    serializer_class = CertificateSerializer

    def get_queryset(self):
        return Certificate.objects.filter(
            user=self.request.user
        ).select_related('course')


# ═════════════════════════════════════════════════════════
#  Paiement cours — API (JWT, retour JSON pour Flutter)
# ═════════════════════════════════════════════════════════

class CourseStripeInitAPIView(APIView):
    """POST /api/academy/courses/<slug>/pay/stripe/init/"""

    def post(self, request, slug):
        from apps.payments.models import Transaction
        from apps.payments.stripe_service import StripeService

        course = get_object_or_404(Course, slug=slug, is_published=True)
        if course.is_free:
            return Response({'error': 'Ce cours est gratuit.'}, status=status.HTTP_400_BAD_REQUEST)

        enrollment, _ = Enrollment.objects.get_or_create(
            user=request.user, course=course,
            defaults={'payment_status': 'pending'},
        )
        if enrollment.payment_status == 'paid':
            return Response({'error': 'Vous êtes déjà inscrit à ce cours.'}, status=status.HTTP_400_BAD_REQUEST)

        transaction, _ = Transaction.objects.get_or_create(
            enrollment=enrollment,
            defaults={'amount': course.price, 'currency': 'HTG'},
        )
        if transaction.status == 'completed':
            return Response({'error': 'Paiement déjà confirmé.'}, status=status.HTTP_400_BAD_REQUEST)

        # Réutiliser un PaymentIntent existant si possible
        existing_pi = transaction.meta_data.get('stripe_payment_intent_id')
        if existing_pi:
            svc    = StripeService()
            result = svc.retrieve_payment_intent(existing_pi)
            if result['success'] and result['status'] not in ('canceled', 'requires_payment_method'):
                return Response({
                    'client_secret': transaction.meta_data.get('stripe_client_secret'),
                    'transaction_number': transaction.transaction_number,
                })

        svc    = StripeService()
        result = svc.create_payment_intent(
            amount_htg=float(course.price),
            transaction_number=transaction.transaction_number,
            metadata={'enrollment_id': str(enrollment.id), 'course_slug': slug},
        )
        if not result['success']:
            return Response(
                {'error': result.get('error', 'Erreur Stripe')},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        transaction.meta_data['stripe_payment_intent_id'] = result['payment_intent_id']
        transaction.meta_data['stripe_client_secret']     = result['client_secret']
        transaction.payment_method = 'credit_card'
        transaction.save(update_fields=['meta_data', 'payment_method', 'updated_at'])

        return Response({
            'client_secret': result['client_secret'],
            'transaction_number': transaction.transaction_number,
        })


class CourseStripeConfirmAPIView(APIView):
    """POST /api/academy/courses/<slug>/pay/stripe/confirm/
    Appeler après confirmation côté Flutter (flutter_stripe).
    Body : { "payment_intent_id": "pi_xxx" }
    """

    def post(self, request, slug):
        from apps.payments.models import Transaction
        from apps.payments.stripe_service import StripeService
        from web.views.payment_views import process_successful_payment

        pi_id = request.data.get('payment_intent_id', '').strip()
        if not pi_id:
            return Response({'error': 'payment_intent_id requis.'}, status=status.HTTP_400_BAD_REQUEST)

        svc    = StripeService()
        result = svc.retrieve_payment_intent(pi_id)
        if not result['success'] or result['status'] != 'succeeded':
            return Response({'error': 'Paiement non confirmé par Stripe.'}, status=status.HTTP_400_BAD_REQUEST)

        tx_number = result.get('transaction_number', '')
        try:
            transaction = Transaction.objects.select_related(
                'enrollment__user', 'enrollment__course'
            ).get(transaction_number=tx_number)
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        if transaction.enrollment.user != request.user:
            return Response({'error': 'Non autorisé.'}, status=status.HTTP_403_FORBIDDEN)

        process_successful_payment(transaction, external_id=pi_id, method='credit_card')
        return Response(EnrollmentSerializer(transaction.enrollment).data)


class CoursePlopPlopInitAPIView(APIView):
    """POST /api/academy/courses/<slug>/pay/plopplop/
    Body : { "method": "moncash" }  — moncash | natcash | kashpaw | all
    Retourne : { "redirect_url": "...", "transaction_number": "..." }
    """

    def post(self, request, slug):
        from apps.payments.models import Transaction
        from apps.payments.plopplop_service import PlopPlopService

        course = get_object_or_404(Course, slug=slug, is_published=True)
        if course.is_free:
            return Response({'error': 'Ce cours est gratuit.'}, status=status.HTTP_400_BAD_REQUEST)

        enrollment, _ = Enrollment.objects.get_or_create(
            user=request.user, course=course,
            defaults={'payment_status': 'pending'},
        )
        if enrollment.payment_status == 'paid':
            return Response({'error': 'Vous êtes déjà inscrit à ce cours.'}, status=status.HTTP_400_BAD_REQUEST)

        transaction, _ = Transaction.objects.get_or_create(
            enrollment=enrollment,
            defaults={'amount': course.price, 'currency': 'HTG'},
        )
        if transaction.status == 'completed':
            return Response({'error': 'Paiement déjà confirmé.'}, status=status.HTTP_400_BAD_REQUEST)

        method = request.data.get('method', 'all')
        svc    = PlopPlopService()
        result = svc.create_payment(
            reference_id=transaction.transaction_number,
            montant=float(course.price),
            payment_method=method,
        )
        if not result['success']:
            return Response(
                {'error': result.get('error', 'Erreur PlopPlop')},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        transaction.payment_method = method if method != 'all' else 'moncash'
        transaction.meta_data['plopplop_url']            = result['url']
        transaction.meta_data['plopplop_transaction_id'] = result.get('transaction_id', '')
        transaction.save(update_fields=['payment_method', 'meta_data', 'updated_at'])

        return Response({
            'redirect_url': result['url'],
            'transaction_number': transaction.transaction_number,
        })


class CoursePlopPlopRetourAPIView(APIView):
    """GET /api/academy/courses/<slug>/pay/plopplop/retour/?reference_id=...
    Appelé après retour depuis WebView PlopPlop.
    Vérifie le paiement et confirme l'enrollment.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        from apps.payments.models import Transaction
        from apps.payments.plopplop_service import PlopPlopService
        from web.views.payment_views import process_successful_payment

        reference_id = request.GET.get('reference_id', '').strip()
        if not reference_id:
            return Response({'error': 'reference_id manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transaction = Transaction.objects.select_related(
                'enrollment__user', 'enrollment__course'
            ).get(transaction_number=reference_id)
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        if transaction.status == 'completed':
            return Response({
                'status': 'already_paid',
                'enrollment': EnrollmentSerializer(transaction.enrollment).data,
            })

        svc    = PlopPlopService()
        result = svc.verify_payment(reference_id)
        if not result['success'] or not result['paid']:
            return Response(
                {'error': 'Paiement non confirmé par PlopPlop.'},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        process_successful_payment(
            transaction,
            external_id=result.get('id_transaction', ''),
            method=result.get('method', transaction.payment_method),
        )
        return Response({
            'status': 'paid',
            'enrollment': EnrollmentSerializer(transaction.enrollment).data,
        })


# ═════════════════════════════════════════════════════════
#  Admin — CRUD Cours
# ═════════════════════════════════════════════════════════

class AdminCourseListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/academy/admin/courses/"""
    serializer_class = AdminCourseSerializer
    permission_classes = [IsAdmin]
    queryset = Course.objects.all().prefetch_related('lessons', 'enrollments')
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_fields = ['level', 'is_published']
    search_fields = ['title']
    ordering_fields = ['created_at', 'title']


class AdminCourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/academy/admin/courses/<slug>/"""
    serializer_class = AdminCourseSerializer
    permission_classes = [IsAdmin]
    queryset = Course.objects.all()
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = 'slug'


# ═════════════════════════════════════════════════════════
#  Admin — CRUD Leçons
# ═════════════════════════════════════════════════════════

class AdminLessonListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/academy/admin/lessons/"""
    serializer_class = AdminLessonSerializer
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_fields = ['course']
    ordering_fields = ['order']

    def get_queryset(self):
        return Lesson.objects.select_related('course').prefetch_related('videos').all()

    def perform_create(self, serializer):
        lesson = serializer.save()
        # Auto-extract PDF si mode extract
        if lesson.pdf_file and lesson.pdf_display_mode == Lesson.PDF_DISPLAY_EXTRACT:
            try:
                from pypdf import PdfReader
                reader = PdfReader(lesson.pdf_file)
                pages  = len(reader.pages)
                lesson.pdf_reading_minutes = max(1, round(pages * 250 / 200))
                lesson.save(update_fields=['pdf_reading_minutes'])
                lesson.sync_duration()
            except Exception as e:
                logger.warning('PDF extract failed on lesson create: %s', e)


class AdminLessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/academy/admin/lessons/<id>/"""
    serializer_class = AdminLessonSerializer
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Lesson.objects.select_related('course').prefetch_related('videos').all()


# ═════════════════════════════════════════════════════════
#  Admin — Vidéos
# ═════════════════════════════════════════════════════════

class AdminLessonVideoCreateView(generics.CreateAPIView):
    """POST /api/academy/admin/lessons/<pk>/videos/"""
    serializer_class = AdminLessonVideoSerializer
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        lesson = get_object_or_404(Lesson, pk=self.kwargs['pk'])
        video_url = serializer.validated_data.get('video_url', '')
        duration  = serializer.validated_data.get('duration_minutes', 0)
        # Auto-détection durée YouTube si non fournie
        if not duration and video_url:
            try:
                from web.views.admin_views import _get_youtube_duration_minutes
                duration, _ = _get_youtube_duration_minutes(video_url)
            except Exception:
                pass
        serializer.save(lesson=lesson, duration_minutes=duration or 0)


class AdminVideoDeleteView(generics.DestroyAPIView):
    """DELETE /api/academy/admin/videos/<id>/"""
    permission_classes = [IsAdmin]
    queryset = LessonVideo.objects.all()
