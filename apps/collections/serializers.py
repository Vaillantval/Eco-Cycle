from rest_framework import serializers
from .models import PickupRequest


class PickupRequestSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.full_name')
    collector_name = serializers.ReadOnlyField(source='collector.full_name')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    slot_display = serializers.ReadOnlyField(source='get_preferred_slot_display')

    class Meta:
        model = PickupRequest
        fields = [
            'id', 'user', 'user_name', 'listing', 'collector', 'collector_name',
            'address', 'city', 'latitude', 'longitude',
            'preferred_date', 'preferred_slot', 'slot_display', 'special_instructions',
            'status', 'status_display', 'status_history',
            'actual_weight_kg', 'collector_notes', 'completion_photo',
            'created_at', 'updated_at', 'completed_at',
        ]
        read_only_fields = [
            'id', 'user', 'collector', 'status', 'status_history',
            'created_at', 'updated_at', 'completed_at',
        ]


class CreatePickupRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PickupRequest
        fields = [
            'listing', 'address', 'city', 'latitude', 'longitude',
            'preferred_date', 'preferred_slot', 'special_instructions',
        ]

    def validate_listing(self, value):
        request = self.context.get('request')
        if value and request and value.user != request.user:
            raise serializers.ValidationError('Ce listing ne vous appartient pas.')
        return value


class AssignCollectorSerializer(serializers.Serializer):
    collector_id = serializers.UUIDField()

    def validate_collector_id(self, value):
        from apps.accounts.models import User
        try:
            user = User.objects.get(id=value, role__in=['collector', 'admin'], is_active=True)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError('Collecteur invalide ou inactif.')

    def validate(self, attrs):
        attrs['collector'] = attrs.pop('collector_id')
        return attrs


class UpdateStatusSerializer(serializers.Serializer):
    STATUS_CHOICES = [
        ('in_transit', 'En transit'),
        ('arrived', 'Arrivé'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
    ]

    status = serializers.ChoiceField(choices=STATUS_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True, default='')
    actual_weight_kg = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, allow_null=True
    )
