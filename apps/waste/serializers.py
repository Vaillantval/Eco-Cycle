from rest_framework import serializers
from .models import WasteListing, WasteCategory, WastePhoto


class WasteCategorySerializer(serializers.ModelSerializer):
    listing_count = serializers.SerializerMethodField()

    class Meta:
        model = WasteCategory
        fields = ['id', 'name', 'slug', 'icon', 'description', 'base_price_per_kg', 'listing_count']

    def get_listing_count(self, obj):
        return obj.listings.filter(status='approved').count()


class WastePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = WastePhoto
        fields = ['id', 'photo', 'order']


class WasteListingSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    user_name = serializers.ReadOnlyField(source='user.full_name')
    additional_photos = WastePhotoSerializer(many=True, read_only=True)

    class Meta:
        model = WasteListing
        fields = [
            'id', 'user', 'user_name', 'category', 'category_name',
            'title', 'description', 'quantity_kg', 'photo', 'photo_url',
            'ai_analysis', 'ai_estimated_value', 'ai_analyzed_at',
            'pickup_address', 'city', 'latitude', 'longitude',
            'status', 'rejection_reason',
            'additional_photos', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'user', 'ai_analysis', 'ai_estimated_value',
            'ai_analyzed_at', 'status', 'rejection_reason', 'created_at', 'updated_at',
        ]


class CreateWasteListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = WasteListing
        fields = [
            'title', 'description', 'category', 'quantity_kg',
            'photo', 'pickup_address', 'city', 'latitude', 'longitude',
        ]

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['status'] = 'pending_review'
        return super().create(validated_data)


class AIAnalysisRequestSerializer(serializers.Serializer):
    image_base64 = serializers.CharField(required=False)
    image_url = serializers.URLField(required=False)

    def validate(self, attrs):
        if not attrs.get('image_base64') and not attrs.get('image_url'):
            raise serializers.ValidationError('Fournir image_base64 ou image_url.')
        return attrs


class AdminReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs['action'] == 'reject' and not attrs.get('rejection_reason'):
            raise serializers.ValidationError({'rejection_reason': 'Raison de rejet requise.'})
        return attrs
