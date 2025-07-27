from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from .models import User, CustomerProfile, ServiceProviderProfile, Vehicle
from .forms import (
    CustomerRegistrationForm, ServiceProviderRegistrationForm,
    CustomerProfileForm, ServiceProviderProfileForm, VehicleForm
)
from bookings.models import ServiceRequest
from reviews.models import Review
import json

def register_view(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 'customer'
            user.save()
            
            # Create customer profile
            CustomerProfile.objects.create(user=user)
            
            # Send verification email (mock for now)
            messages.success(request, 'Registration successful! Please check your email to verify your account.')
            return redirect('accounts:login')
    else:
        form = CustomerRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def provider_register_view(request):
    if request.method == 'POST':
        form = ServiceProviderRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 'service_provider'
            user.save()
            
            # Create service provider profile
            ServiceProviderProfile.objects.create(
                user=user,
                business_name=form.cleaned_data['business_name'],
                business_license=form.cleaned_data['business_license'],
                provider_type=form.cleaned_data['provider_type'],
                description=form.cleaned_data.get('description', ''),
            )
            
            messages.success(request, 'Registration successful! Your account is pending approval.')
            return redirect('accounts:login')
    else:
        form = ServiceProviderRegistrationForm()
    
    return render(request, 'accounts/provider_register.html', {'form': form})

@login_required
def dashboard_view(request):
    user = request.user
    context = {'user': user}
    
    if user.user_type == 'customer':
        try:
            customer_profile = user.customer_profile
            context.update({
                'recent_requests': ServiceRequest.objects.filter(customer=customer_profile)[:5],
                'vehicles': customer_profile.vehicles.all(),
                'pending_reviews': ServiceRequest.objects.filter(
                    customer=customer_profile,
                    status='completed',
                    review__isnull=True
                )[:3]
            })
        except CustomerProfile.DoesNotExist:
            CustomerProfile.objects.create(user=user)
            
        return render(request, 'accounts/customer_dashboard.html', context)
        
    elif user.user_type == 'service_provider':
        try:
            provider_profile = user.service_provider_profile
            context.update({
                'provider_profile': provider_profile,
                'pending_requests': ServiceRequest.objects.filter(
                    service__provider=provider_profile,
                    status='pending'
                )[:5],
                'active_requests': ServiceRequest.objects.filter(
                    service_provider=provider_profile,
                    status__in=['accepted', 'in_progress']
                )[:5],
                'recent_reviews': Review.objects.filter(service_provider=provider_profile)[:5],
                'unpaid_commissions': provider_profile.commissions.filter(status='pending').count()
            })
        except ServiceProviderProfile.DoesNotExist:
            messages.error(request, 'Service provider profile not found.')
            
        return render(request, 'accounts/provider_dashboard.html', context)
        
    elif user.user_type == 'admin':
        context.update({
            'total_customers': User.objects.filter(user_type='customer').count(),
            'total_providers': User.objects.filter(user_type='service_provider').count(),
            'pending_approvals': ServiceProviderProfile.objects.filter(is_approved=False).count(),
            'recent_requests': ServiceRequest.objects.all()[:10],
        })
        return render(request, 'accounts/admin_dashboard.html', context)
    
    return render(request, 'accounts/dashboard.html', context)

@login_required
def profile_view(request):
    user = request.user
    
    if user.user_type == 'customer':
        try:
            profile = user.customer_profile
        except CustomerProfile.DoesNotExist:
            profile = CustomerProfile.objects.create(user=user)
            
        if request.method == 'POST':
            form = CustomerProfileForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('accounts:profile')
        else:
            form = CustomerProfileForm(instance=user)
            
        return render(request, 'accounts/customer_profile.html', {
            'form': form,
            'profile': profile,
            'vehicles': profile.vehicles.all()
        })
        
    elif user.user_type == 'service_provider':
        return redirect('accounts:provider_profile')
    
    return render(request, 'accounts/profile.html', {'user': user})

@login_required
def provider_profile_view(request):
    if request.user.user_type != 'service_provider':
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    try:
        profile = request.user.service_provider_profile
    except ServiceProviderProfile.DoesNotExist:
        messages.error(request, 'Service provider profile not found.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = ServiceProviderProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:provider_profile')
    else:
        form = ServiceProviderProfileForm(instance=request.user)
    
    return render(request, 'accounts/provider_profile.html', {
        'form': form,
        'profile': profile,
        'services': profile.services.all()
    })

def verify_email(request, token):
    # Mock email verification
    messages.success(request, 'Email verified successfully!')
    return redirect('accounts:login')