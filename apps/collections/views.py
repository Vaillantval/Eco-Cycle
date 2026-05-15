from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import PickupRequest
from .serializers import (
    PickupRequestSerializer, CreatePickupRequestSerializer,
    AssignCollectorSerializer, UpdateStatusSerializer,
)
from apps.accounts.permissions import IsAdmin, IsCollector, IsOwnerOrAdmin


class PickupRequestListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/collections/  — Mes demandes de ramassage
    POST /api/collections/  — Créer une demande
    """
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreatePickupRequestSerializer
        return PickupRequestSerializer

    def get_queryset(self):
        return PickupRequest.objects.filter(
            user=self.request.user
        ).select_related('collector', 'listing')

    def perform_create(self, serializer):
        pickup = serializer.save(user=self.request.user)
        from apps.notifications.tasks import notify_admin_new_pickup
        notify_admin_new_pickup.delay(str(pickup.id))


class PickupRequestDetailView(generics.RetrieveAPIView):
    """GET /api/collections/<id>/"""
    serializer_class = PickupRequestSerializer
    permission_classes = [IsOwnerOrAdmin]
    queryset = PickupRequest.objects.select_related('collector', 'listing', 'user')


class AdminPickupListView(generics.ListAPIView):
    """GET /api/collections/admin/ — Toutes les demandes (admin)"""
    serializer_class = PickupRequestSerializer
    permission_classes = [IsAdmin]
    queryset = PickupRequest.objects.select_related('user', 'collector', 'listing').all()
    filterset_fields = ['status', 'city', 'preferred_date']
    search_fields = ['user__email', 'user__first_name', 'city', 'address']
    ordering_fields = ['created_at', 'preferred_date']


class AssignCollectorView(APIView):
    """POST /api/collections/<id>/assign/ — Assigner un ramasseur (admin)"""
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        pickup = get_object_or_404(PickupRequest, pk=pk)
        serializer = AssignCollectorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        collector = serializer.validated_data['collector']
        pickup.collector = collector
        pickup.update_status('assigned', f'Assigné à {collector.full_name}')
        from apps.notifications.tasks import notify_collector_assigned
        notify_collector_assigned.delay(str(pickup.id))
        return Response(PickupRequestSerializer(pickup).data)


class CollectorPickupListView(generics.ListAPIView):
    """GET /api/collections/collector/ — Ramassages assignés au collecteur"""
    serializer_class = PickupRequestSerializer
    permission_classes = [IsCollector]

    def get_queryset(self):
        return PickupRequest.objects.filter(
            collector=self.request.user,
            status__in=['assigned', 'in_transit', 'arrived'],
        ).select_related('user', 'listing')


class UpdatePickupStatusView(APIView):
    """POST /api/collections/<id>/status/ — Mettre à jour le statut (collecteur)"""
    permission_classes = [IsCollector]

    def post(self, request, pk):
        pickup = get_object_or_404(PickupRequest, pk=pk, collector=request.user)
        serializer = UpdateStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pickup.update_status(
            serializer.validated_data['status'],
            serializer.validated_data.get('note', ''),
        )

        if serializer.validated_data.get('actual_weight_kg') is not None:
            pickup.actual_weight_kg = serializer.validated_data['actual_weight_kg']
            pickup.save()

        from apps.notifications.tasks import notify_pickup_status_update
        notify_pickup_status_update.delay(str(pickup.id))

        return Response(PickupRequestSerializer(pickup).data)
