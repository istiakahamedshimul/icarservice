from rest_framework import serializers
from services.models import Service, ServiceCategory
from bookings.models import ServiceRequest
from reviews.models import Review
from accounts.models import ServiceProviderProfile

class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'description', 'icon']

class ServiceProviderSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='service_provider_profile.business_name')
    provider_type = serializers.CharField(source='service_provider_profile.get_provider_type_display')
    rating = serializers.DecimalField(source='service_provider_profile.rating', max_digits=3, decimal_places=2)
    
    class Meta:
        model = ServiceProviderProfile
        fields = ['id', 'business_name', 'provider_type', 'rating']

class ServiceSerializer(serializers.ModelSerializer):
    category = ServiceCategorySerializer(read_only=True)
    provider = ServiceProviderSerializer(read_only=True)
    
    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'base_price', 'category', 'provider', 'estimated_duration']

class ServiceRequestSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    service_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ServiceRequest
        fields = [
            'id', 'service', 'service_id', 'description', 'priority', 'status',
            'pickup_address', 'pickup_latitude', 'pickup_longitude',
            'estimated_cost', 'final_cost', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

class ReviewSerializer(serializers.ModelSerializer):
    service_provider_name = serializers.CharField(source='service_provider.business_name', read_only=True)
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'rating', 'comment', 'quality_rating', 'timeliness_rating',
            'professionalism_rating', 'value_rating', 'service_provider_name',
            'customer_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']