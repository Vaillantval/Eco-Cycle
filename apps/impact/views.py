from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum
from .models import ImpactRecord, UserImpactSummary
from .serializers import ImpactRecordSerializer, UserImpactSummarySerializer


class MyImpactDashboardView(APIView):
    """GET /api/impact/dashboard/"""
    def get(self, request):
        summary, _ = UserImpactSummary.objects.get_or_create(user=request.user)
        records = ImpactRecord.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]
        return Response({
            'summary': UserImpactSummarySerializer(summary).data,
            'recent_records': ImpactRecordSerializer(records, many=True).data,
        })


class LeaderboardView(APIView):
    """GET /api/impact/leaderboard/ — Top 20 recycleurs"""
    def get(self, request):
        top = UserImpactSummary.objects.select_related('user').order_by(
            '-total_kg_recycled'
        )[:20]
        return Response(UserImpactSummarySerializer(top, many=True).data)


class PublicStatsView(APIView):
    """GET /api/impact/stats/ — Stats globales (landing page)"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from apps.accounts.models import User
        from apps.marketplace.models import Order
        from apps.collections.models import PickupRequest

        agg = ImpactRecord.objects.aggregate(
            total_kg=Sum('kg_recycled'),
            total_co2=Sum('co2_saved_kg'),
        )
        return Response({
            'total_kg_recycled': agg['total_kg'] or 0,
            'total_co2_saved_kg': agg['total_co2'] or 0,
            'total_users': User.objects.filter(is_active=True).count(),
            'total_orders': Order.objects.filter(status='completed').count(),
            'total_pickups': PickupRequest.objects.filter(status='completed').count(),
        })
