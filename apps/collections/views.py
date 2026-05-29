from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import PickupRequest, CollectorLocation
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


class UpdateCollectorLocationView(APIView):
    """
    POST /api/collections/<id>/location/
    Le collecteur envoie sa position GPS toutes les ~30s quand il est en transit.
    Body : { "latitude": 18.54, "longitude": -72.34 }
    """
    permission_classes = [IsCollector]

    def post(self, request, pk):
        pickup = get_object_or_404(PickupRequest, pk=pk, collector=request.user)
        if pickup.status not in ('assigned', 'in_transit', 'arrived'):
            return Response(
                {'error': 'Mise à jour GPS non autorisée pour ce statut.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            lat = float(request.data.get('latitude'))
            lon = float(request.data.get('longitude'))
        except (TypeError, ValueError):
            return Response({'error': 'latitude/longitude invalides.'}, status=status.HTTP_400_BAD_REQUEST)

        CollectorLocation.objects.update_or_create(
            pickup=pickup,
            defaults={'collector': request.user, 'latitude': lat, 'longitude': lon},
        )
        return Response({'status': 'ok'})


class GetCollectorLocationView(APIView):
    """
    GET /api/collections/<id>/location/
    Retourne la dernière position GPS du collecteur.
    Accessible par le propriétaire du pickup et les admins.
    """
    permission_classes = [IsOwnerOrAdmin]

    def get(self, request, pk):
        pickup = get_object_or_404(PickupRequest, pk=pk)
        try:
            loc = pickup.collector_location
        except CollectorLocation.DoesNotExist:
            return Response({'latitude': None, 'longitude': None, 'updated_at': None})

        staleness = (timezone.now() - loc.updated_at).total_seconds()
        return Response({
            'latitude':   float(loc.latitude),
            'longitude':  float(loc.longitude),
            'updated_at': loc.updated_at.isoformat(),
            'is_stale':   staleness > 300,
        })


class AdminPickupGeoView(APIView):
    """
    GET /api/collections/admin/geo/
    Retourne les coordonnées GPS de tous les pickups pour la heatmap admin.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        status_filter = request.GET.get('status', '')
        qs = PickupRequest.objects.exclude(latitude__isnull=True).select_related('user', 'collector')
        if status_filter:
            qs = qs.filter(status=status_filter)

        points = []
        for p in qs:
            entry = {
                'id':        str(p.id),
                'lat':       float(p.latitude),
                'lon':       float(p.longitude),
                'status':    p.status,
                'city':      p.city,
                'user':      p.user.full_name,
                'date':      p.preferred_date.isoformat(),
                'collector': p.collector.full_name if p.collector else None,
            }
            if hasattr(p, 'collector_location'):
                entry['collector_lat'] = float(p.collector_location.latitude)
                entry['collector_lon'] = float(p.collector_location.longitude)
            points.append(entry)

        return Response({'points': points, 'total': len(points)})
