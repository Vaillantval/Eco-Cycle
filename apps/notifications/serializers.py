from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.ReadOnlyField(source='get_notification_type_display')

    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'type_display',
            'title', 'message', 'data', 'is_read', 'created_at',
        ]
        read_only_fields = ['id', 'notification_type', 'title', 'message', 'data', 'created_at']
