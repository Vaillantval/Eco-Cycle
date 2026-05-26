from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import WasteListing, WasteCategory
from .serializers import (
    WasteListingSerializer, CreateWasteListingSerializer,
    WasteCategorySerializer, AIAnalysisRequestSerializer, AdminReviewSerializer,
)
from .ai_service import ai_service, recycling_advisor
from .tasks import analyze_waste_photo_async, notify_admin_new_listing
from apps.accounts.permissions import IsAdmin, IsOwnerOrAdmin


class WasteCategoryListView(generics.ListAPIView):
    """GET /api/waste/categories/"""
    serializer_class = WasteCategorySerializer
    permission_classes = [permissions.AllowAny]
    queryset = WasteCategory.objects.filter(is_active=True)


class WasteListingListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/waste/listings/  — Listings de l'utilisateur connecté
    POST /api/waste/listings/  — Créer un nouveau listing
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateWasteListingSerializer
        return WasteListingSerializer

    def get_queryset(self):
        return WasteListing.objects.filter(user=self.request.user).select_related('category')

    def perform_create(self, serializer):
        listing = serializer.save()
        analyze_waste_photo_async.delay(str(listing.id))
        notify_admin_new_listing.delay(str(listing.id))


class WasteListingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/waste/listings/<id>/"""
    serializer_class = WasteListingSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        return WasteListing.objects.select_related('category', 'user')


class AIAnalysisView(APIView):
    """
    POST /api/waste/analyze/
    Analyse une image via Claude Vision — preview avant soumission.
    """
    throttle_scope = 'ai_analysis'

    def post(self, request):
        serializer = AIAnalysisRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get('image_base64'):
            result = ai_service.analyze_image_from_base64(serializer.validated_data['image_base64'])
        else:
            result = ai_service.analyze_image_from_url(serializer.validated_data['image_url'])

        if 'error' in result:
            return Response({'error': result['error']}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        return Response({'analysis': result})


class RecyclingAdvisorView(APIView):
    """
    POST /api/waste/advisor/
    Chat conversationnel avec l'agent Conseiller Recyclage.
    """
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'ai_analysis'

    def post(self, request):
        message = request.data.get('message', '').strip()
        history = request.data.get('history', [])

        if not message:
            return Response({'error': 'Message vide.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(message) > 500:
            return Response({'error': 'Message trop long (500 caractères max).'}, status=status.HTTP_400_BAD_REQUEST)

        reply, updated_history = recycling_advisor.chat(message, history)
        return Response({
            'reply': reply,
            'history': updated_history[-10:],
        })


class AdminListingListView(generics.ListAPIView):
    """GET /api/waste/admin/listings/ — Tous les listings (admin)"""
    serializer_class = WasteListingSerializer
    permission_classes = [IsAdmin]
    queryset = WasteListing.objects.select_related('category', 'user').all()
    filterset_fields = ['status', 'category', 'city']
    search_fields = ['title', 'user__email', 'user__first_name']
    ordering_fields = ['created_at', 'ai_estimated_value']


class AdminReviewListingView(APIView):
    """POST /api/waste/admin/listings/<id>/review/ — Approuver ou rejeter"""
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        listing = get_object_or_404(WasteListing, pk=pk)
        serializer = AdminReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        listing.reviewed_by = request.user
        listing.reviewed_at = timezone.now()

        if action == 'approve':
            listing.status = 'approved'
            listing.save()
            from apps.notifications.tasks import notify_listing_approved
            notify_listing_approved.delay(str(listing.id))
        else:
            listing.status = 'rejected'
            listing.rejection_reason = serializer.validated_data.get('rejection_reason', '')
            listing.save()
            from apps.notifications.tasks import notify_listing_rejected
            notify_listing_rejected.delay(str(listing.id))

        return Response(WasteListingSerializer(listing).data)
