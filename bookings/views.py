from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import ServiceRequest, ServiceRequestUpdate
from services.models import Service
from accounts.models import CustomerProfile, ServiceProviderProfile, Vehicle
import json

@login_required
def booking_list_view(request):
    user = request.user
    
    if user.user_type == 'customer':
        try:
            customer = user.customer_profile
            bookings = ServiceRequest.objects.filter(customer=customer).order_by('-created_at')
        except CustomerProfile.DoesNotExist:
            bookings = []
            
    elif user.user_type == 'service_provider':
        try:
            provider = user.service_provider_profile
            bookings = ServiceRequest.objects.filter(service_provider=provider).order_by('-created_at')
        except ServiceProviderProfile.DoesNotExist:
            bookings = []
    else:
        bookings = ServiceRequest.objects.all().order_by('-created_at')
    
    context = {
        'bookings': bookings,
        'user_type': user.user_type,
    }
    
    return render(request, 'bookings/list.html', context)

@login_required
def create_booking_view(request):
    if request.user.user_type != 'customer':
        messages.error(request, 'Only customers can create bookings.')
        return redirect('accounts:dashboard')
    
    try:
        customer = request.user.customer_profile
        vehicles = customer.vehicles.all()
        
        if not vehicles.exists():
            messages.error(request, 'Please add a vehicle to your profile before booking a service.')
            return redirect('accounts:profile')
            
    except CustomerProfile.DoesNotExist:
        messages.error(request, 'Customer profile not found.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        service_id = request.POST.get('service_id')
        vehicle_id = request.POST.get('vehicle_id')
        description = request.POST.get('description')
        priority = request.POST.get('priority', 'medium')
        pickup_address = request.POST.get('pickup_address')
        pickup_latitude = request.POST.get('pickup_latitude')
        pickup_longitude = request.POST.get('pickup_longitude')
        
        service = get_object_or_404(Service, id=service_id, is_available=True)
        vehicle = get_object_or_404(Vehicle, id=vehicle_id, customer=customer)
        
        # Create service request
        service_request = ServiceRequest.objects.create(
            customer=customer,
            service=service,
            vehicle=vehicle,
            description=description,
            priority=priority,
            pickup_address=pickup_address,
            pickup_latitude=pickup_latitude,
            pickup_longitude=pickup_longitude,
            estimated_cost=service.base_price,
        )
        
        # Create initial update
        ServiceRequestUpdate.objects.create(
            service_request=service_request,
            status='pending',
            message='Service request created',
            created_by='customer'
        )
        
        messages.success(request, 'Service request created successfully!')
        return redirect('bookings:detail', booking_id=service_request.id)
    
    # Get available services
    services = Service.objects.filter(is_available=True).select_related('provider', 'category')
    
    context = {
        'services': services,
        'vehicles': vehicles,
    }
    
    return render(request, 'bookings/create.html', context)

def booking_detail_view(request, booking_id):
    booking = get_object_or_404(ServiceRequest, id=booking_id)
    
    # Check access permissions
    user = request.user
    if user.user_type == 'customer':
        if booking.customer.user != user:
            messages.error(request, 'Access denied.')
            return redirect('bookings:list')
    elif user.user_type == 'service_provider':
        if booking.service_provider and booking.service_provider.user != user:
            messages.error(request, 'Access denied.')
            return redirect('bookings:list')
    
    updates = booking.updates.all()
    
    context = {
        'booking': booking,
        'updates': updates,
        'can_update': user.user_type in ['service_provider', 'admin'],
    }
    
    return render(request, 'bookings/detail.html', context)

@login_required
def update_booking_status(request, booking_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    booking = get_object_or_404(ServiceRequest, id=booking_id)
    new_status = request.POST.get('status')
    message = request.POST.get('message', '')
    
    # Check permissions
    user = request.user
    if user.user_type == 'service_provider':
        if booking.service_provider and booking.service_provider.user != user:
            return JsonResponse({'error': 'Access denied'}, status=403)
    elif user.user_type != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Update booking status
    booking.update_status(new_status, user)
    
    # Create update record
    ServiceRequestUpdate.objects.create(
        service_request=booking,
        status=new_status,
        message=message,
        created_by='provider' if user.user_type == 'service_provider' else 'admin'
    )
    
    return JsonResponse({'success': True, 'status': new_status})

@login_required
def cancel_booking_view(request, booking_id):
    booking = get_object_or_404(ServiceRequest, id=booking_id)
    
    # Check permissions - only customer or admin can cancel
    if request.user.user_type == 'customer':
        if booking.customer.user != request.user:
            messages.error(request, 'Access denied.')
            return redirect('bookings:list')
    elif request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('bookings:list')
    
    if booking.status in ['completed', 'cancelled']:
        messages.error(request, f'Cannot cancel a {booking.status} booking.')
        return redirect('bookings:detail', booking_id=booking.id)
    
    if request.method == 'POST':
        cancellation_reason = request.POST.get('reason', '')
        booking.status = 'cancelled'
        booking.cancellation_reason = cancellation_reason
        booking.save()
        
        # Create update record
        ServiceRequestUpdate.objects.create(
            service_request=booking,
            status='cancelled',
            message=f'Booking cancelled: {cancellation_reason}',
            created_by='customer' if request.user.user_type == 'customer' else 'admin'
        )
        
        messages.success(request, 'Booking cancelled successfully.')
        return redirect('bookings:detail', booking_id=booking.id)
    
    return render(request, 'bookings/cancel.html', {'booking': booking})

@login_required
def provider_requests_view(request):
    if request.user.user_type != 'service_provider':
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    try:
        provider = request.user.service_provider_profile
        
        # Get pending requests for services provided by this provider
        pending_requests = ServiceRequest.objects.filter(
            service__provider=provider,
            status='pending'
        ).order_by('-created_at')
        
        # Get accepted/active requests
        active_requests = ServiceRequest.objects.filter(
            service_provider=provider,
            status__in=['accepted', 'in_progress']
        ).order_by('-accepted_at')
        
    except ServiceProviderProfile.DoesNotExist:
        messages.error(request, 'Service provider profile not found.')
        return redirect('accounts:dashboard')
    
    context = {
        'pending_requests': pending_requests,
        'active_requests': active_requests,
        'provider': provider,
    }
    
    return render(request, 'bookings/provider_requests.html', context)

@login_required
def accept_request_view(request, request_id):
    if request.user.user_type != 'service_provider':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        provider = request.user.service_provider_profile
        service_request = get_object_or_404(
            ServiceRequest,
            id=request_id,
            service__provider=provider,
            status='pending'
        )
        
        # Check if provider is eligible
        if not provider.is_eligible_for_requests:
            return JsonResponse({
                'error': 'You have unpaid dues. Please clear them to accept new requests.'
            }, status=403)
        
        # Accept the request
        service_request.service_provider = provider
        service_request.status = 'accepted'
        service_request.accepted_at = timezone.now()
        service_request.save()
        
        # Create update record
        ServiceRequestUpdate.objects.create(
            service_request=service_request,
            status='accepted',
            message='Service request accepted',
            created_by='provider'
        )
        
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': True})
        
        messages.success(request, 'Service request accepted successfully!')
        return redirect('bookings:provider_requests')
        
    except ServiceProviderProfile.DoesNotExist:
        return JsonResponse({'error': 'Service provider profile not found'}, status=404)

@login_required
def reject_request_view(request, request_id):
    if request.user.user_type != 'service_provider':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        provider = request.user.service_provider_profile
        service_request = get_object_or_404(
            ServiceRequest,
            id=request_id,
            service__provider=provider,
            status='pending'
        )
        
        rejection_reason = request.POST.get('reason', 'No reason provided')
        
        service_request.status = 'rejected'
        service_request.cancellation_reason = rejection_reason
        service_request.save()
        
        # Create update record
        ServiceRequestUpdate.objects.create(
            service_request=service_request,
            status='rejected',
            message=f'Service request rejected: {rejection_reason}',
            created_by='provider'
        )
        
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': True})
        
        messages.success(request, 'Service request rejected.')
        return redirect('bookings:provider_requests')
        
    except ServiceProviderProfile.DoesNotExist:
        return JsonResponse({'error': 'Service provider profile not found'}, status=404)