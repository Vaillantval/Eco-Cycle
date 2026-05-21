from rest_framework import generics, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User
from .permissions import IsAdmin


# ─────────────────────────────────────────────────────────
#  Serializers (inline — scope admin uniquement)
# ─────────────────────────────────────────────────────────

class AdminUserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'first_name', 'last_name',
            'phone', 'role', 'is_active', 'is_email_verified',
            'city', 'avatar', 'created_at',
        ]
        read_only_fields = ['id', 'email', 'is_email_verified', 'created_at']


class AdminUserPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['role', 'is_active', 'first_name', 'last_name', 'phone', 'city']

    def validate_role(self, value):
        if value not in ('user', 'collector', 'admin'):
            raise serializers.ValidationError('Rôle invalide.')
        return value


# ─────────────────────────────────────────────────────────
#  GET /api/admin/stats/
# ─────────────────────────────────────────────────────────

class AdminStatsView(APIView):
    """Statistiques globales pour le dashboard admin mobile."""
    permission_classes = [IsAdmin]

    def get(self, request):
        from django.utils import timezone
        from django.db.models import Sum
        from apps.waste.models import WasteListing
        from apps.collections.models import PickupRequest
        from apps.marketplace.models import Auction, Order
        from apps.academy.models import Enrollment

        today = timezone.now().date()
        revenue = (
            Order.objects.filter(status='paid')
            .aggregate(total=Sum('amount'))['total'] or 0
        )

        return Response({
            'listings_pending':       WasteListing.objects.filter(status='pending_review').count(),
            'pickups_active':         PickupRequest.objects.filter(
                                          status__in=['assigned', 'in_transit', 'arrived']
                                      ).count(),
            'auctions_active':        Auction.objects.filter(status='active').count(),
            'marketplace_revenue_htg': float(revenue),
            'academy_enrollments':    Enrollment.objects.count(),
            'new_users_today':        User.objects.filter(created_at__date=today).count(),
            'total_users':            User.objects.filter(is_active=True).count(),
        })


# ─────────────────────────────────────────────────────────
#  GET /api/admin/users/
#  GET /PATCH /api/admin/users/<id>/
# ─────────────────────────────────────────────────────────

class AdminUserListView(generics.ListAPIView):
    """Liste tous les utilisateurs (admin)."""
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]
    queryset = User.objects.all()
    filterset_fields = ['role', 'is_active', 'is_email_verified']
    search_fields = ['email', 'first_name', 'last_name', 'city']
    ordering_fields = ['created_at', 'email', 'role']


class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    """Lire et modifier un utilisateur (rôle, statut actif...)."""
    permission_classes = [IsAdmin]
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return AdminUserPatchSerializer
        return AdminUserSerializer


# ─────────────────────────────────────────────────────────
#  GET /api/admin/collectors/
# ─────────────────────────────────────────────────────────

class AdminCollectorListView(generics.ListAPIView):
    """Liste des collecteurs (et admins) actifs — pour assignment ramassage."""
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]
    queryset = User.objects.filter(role__in=['collector', 'admin'], is_active=True)
    search_fields = ['email', 'first_name', 'last_name', 'city']
    ordering_fields = ['first_name', 'city']
