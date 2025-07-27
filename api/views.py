from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from geopy.distance import geodesic
from services.models import Service, ServiceCategory
from bookings.models import ServiceRequest
from reviews.models import Review
from accounts.models import ServiceProviderProfile
from . import serializers

class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.filter(is_available=True)
    serializer_class = serializers.ServiceSerializer
    permission_classes = [IsAuthenticated]

class ServiceRequestViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ServiceRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'customer':
            return ServiceRequest.objects.filter(customer=user.customer_profile)
        elif user.user_type == 'service_provider':
            return ServiceRequest.objects.filter(service_provider=user.service_provider_profile)
        return ServiceRequest.objects.all()

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'customer':
            return Review.objects.filter(customer=user.customer_profile)
        elif user.user_type == 'service_provider':
            return Review.objects.filter(service_provider=user.service_provider_profile)
        return Review.objects.all()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nearby_services_api(request):
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')
    radius = float(request.GET.get('radius', 10))
    
    if not user_lat or not user_lng:
        return Response({'error': 'Location required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user_lat, user_lng = float(user_lat), float(user_lng)
    user_location = (user_lat, user_lng)
    
    providers = ServiceProviderProfile.objects.filter(
        is_approved=True,
        is_active=True,
        is_eligible_for_requests=True
    ).exclude(user__latitude__isnull=True, user__longitude__isnull=True)
    
    nearby_providers = []
    for provider in providers:
        provider_location = (float(provider.user.latitude), float(provider.user.longitude))
        distance = geodesic(user_location, provider_location).kilometers
        
        if distance <= radius:
            provider_data = {
                'id': provider.id,
                'business_name': provider.business_name,
                'provider_type': provider.get_provider_type_display(),
                'rating': float(provider.rating),
                'distance': round(distance, 2),
                'latitude': float(provider.user.latitude),
                'longitude': float(provider.user.longitude),
                'services': serializers.ServiceSerializer(
                    provider.services.filter(is_available=True), many=True
                ).data
            }
            nearby_providers.append(provider_data)
    
    nearby_providers.sort(key=lambda x: x['distance'])
    return Response({'providers': nearby_providers})

@api_view(['GET'])
def service_categories_api(request):
    categories = ServiceCategory.objects.filter(is_active=True)
    data = serializers.ServiceCategorySerializer(categories, many=True).data
    return Response(data)