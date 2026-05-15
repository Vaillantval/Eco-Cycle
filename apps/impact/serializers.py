from rest_framework import serializers
from .models import ImpactRecord, UserImpactSummary


class ImpactRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImpactRecord
        fields = [
            'id', 'category_slug', 'kg_recycled',
            'co2_saved_kg', 'economic_value_htg', 'created_at',
        ]


class UserImpactSummarySerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.full_name')
    user_email = serializers.ReadOnlyField(source='user.email')
    user_avatar = serializers.ImageField(source='user.avatar', read_only=True)

    class Meta:
        model = UserImpactSummary
        fields = [
            'user', 'user_name', 'user_email', 'user_avatar',
            'total_kg_recycled', 'total_co2_saved_kg',
            'total_economic_value_htg', 'total_transactions',
            'community_rank', 'updated_at',
        ]
