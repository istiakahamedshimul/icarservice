from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg
from geopy.distance import geodesic
from .models import Service, ServiceCategory, ServiceArea
from accounts.models import ServiceProviderProfile
from reviews.models import Review
import json

def service_list_view(request):
    categories = ServiceCategory.objects.filter(is_active=True)
    services = Service.objects.filter(is_available=True).select_related('provider', 'category')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        services = services.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(provider__business_name__icontains=search_query)
        )
    
    # Category filter
    category_id = request.GET.get('category')
    if category_id:
        services = services.filter(category_id=category_id)
    
    context = {
        'services': services,
        'categories': categories,
        'search_query': search_query,
        'selected_category': int(category_id) if category_id else None,
    }
    
    return render(request, 'services/list.html', context)

def nearby_services_view(request):
    # Get user location from request
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')
    radius = float(request.GET.get('radius', 10))  # Default 10km radius
    
    if not user_lat or not user_lng:
        return JsonResponse({'error': 'Location required'}, status=400)
    
    user_lat, user_lng = float(user_lat), float(user_lng)
    user_location = (user_lat, user_lng)
    
    # Get all service providers with their locations
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
                'services': [
                    {
                        'id': service.id,
                        'name': service.name,
                        'base_price': float(service.base_price),
                        'category': service.category.name
                    }
                    for service in provider.services.filter(is_available=True)
                ]
            }
            nearby_providers.append(provider_data)
    
    # Sort by distance
    nearby_providers.sort(key=lambda x: x['distance'])
    
    if request.headers.get('Content-Type') == 'application/json':
        return JsonResponse({'providers': nearby_providers})
    
    return render(request, 'services/nearby.html', {'providers': nearby_providers})

def services_by_category(request, category_id):
    category = get_object_or_404(ServiceCategory, id=category_id, is_active=True)
    services = Service.objects.filter(category=category, is_available=True).select_related('provider')
    
    context = {
        'category': category,
        'services': services,
    }
    
    return render(request, 'services/by_category.html', context)

def provider_detail_view(request, provider_id):
    provider = get_object_or_404(ServiceProviderProfile, id=provider_id, is_approved=True)
    services = provider.services.filter(is_available=True)
    reviews = Review.objects.filter(service_provider=provider, is_approved=True)[:5]
    
    # Calculate average ratings
    avg_ratings = reviews.aggregate(
        avg_quality=Avg('quality_rating'),
        avg_timeliness=Avg('timeliness_rating'),
        avg_professionalism=Avg('professionalism_rating'),
        avg_value=Avg('value_rating')
    )
    
    context = {
        'provider': provider,
        'services': services,
        'reviews': reviews,
        'avg_ratings': avg_ratings,
    }
    
    return render(request, 'services/provider_detail.html', context)

@login_required
def manage_services_view(request):
    if request.user.user_type != 'service_provider':
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    try:
        provider = request.user.service_provider_profile
        services = provider.services.all()
    except ServiceProviderProfile.DoesNotExist:
        messages.error(request, 'Service provider profile not found.')
        return redirect('accounts:dashboard')
    
    context = {
        'services': services,
        'provider': provider,
    }
    
    return render(request, 'services/manage.html', context)

@login_required
def add_service_view(request):
    if request.user.user_type != 'service_provider':
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    try:
        provider = request.user.service_provider_profile
    except ServiceProviderProfile.DoesNotExist:
        messages.error(request, 'Service provider profile not found.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        # Handle service creation
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description', '')
        base_price = request.POST.get('base_price')
        
        category = get_object_or_404(ServiceCategory, id=category_id)
        
        Service.objects.create(
            provider=provider,
            category=category,
            name=name,
            description=description,
            base_price=base_price,
        )
        
        messages.success(request, 'Service added successfully!')
        return redirect('services:manage')
    
    categories = ServiceCategory.objects.filter(is_active=True)
    return render(request, 'services/add.html', {'categories': categories})

@login_required
def edit_service_view(request, service_id):
    if request.user.user_type != 'service_provider':
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    try:
        provider = request.user.service_provider_profile
        service = get_object_or_404(Service, id=service_id, provider=provider)
    except ServiceProviderProfile.DoesNotExist:
        messages.error(request, 'Service provider profile not found.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        service.name = request.POST.get('name')
        service.category_id = request.POST.get('category')
        service.description = request.POST.get('description', '')
        service.base_price = request.POST.get('base_price')
        service.is_available = request.POST.get('is_available') == 'on'
        service.save()
        
        messages.success(request, 'Service updated successfully!')
        return redirect('services:manage')
    
    categories = ServiceCategory.objects.filter(is_active=True)
    return render(request, 'services/edit.html', {
        'service': service,
        'categories': categories
    })

@login_required
def delete_service_view(request, service_id):
    if request.user.user_type != 'service_provider':
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    try:
        provider = request.user.service_provider_profile
        service = get_object_or_404(Service, id=service_id, provider=provider)
        service.delete()
        messages.success(request, 'Service deleted successfully!')
    except ServiceProviderProfile.DoesNotExist:
        messages.error(request, 'Service provider profile not found.')
    
    return redirect('services:manage')