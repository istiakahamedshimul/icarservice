#!/usr/bin/env python
"""Management commands for Vehicle Service Platform"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vehicle_service_platform.settings')
django.setup()

from django.contrib.auth import get_user_model
from services.models import ServiceCategory
from accounts.models import ServiceProviderProfile, CustomerProfile

User = get_user_model()

def create_superuser():
    """Create a superuser for admin access"""
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@servicehub.com',
            password='admin123',
            user_type='admin'
        )
        print("✅ Superuser created: admin/admin123")
    else:
        print("ℹ️ Superuser already exists")

def create_service_categories():
    """Create default service categories"""
    categories = [
        {'name': 'Mechanical Services', 'description': 'Car repairs and maintenance', 'icon': 'fas fa-wrench'},
        {'name': 'Fuel Delivery', 'description': 'Emergency fuel delivery service', 'icon': 'fas fa-gas-pump'},
        {'name': 'Towing Services', 'description': '24/7 towing and roadside assistance', 'icon': 'fas fa-truck'},
        {'name': 'Car Wash', 'description': 'Professional car washing and detailing', 'icon': 'fas fa-car'},
        {'name': 'Parts & Accessories', 'description': 'Vehicle parts and accessories', 'icon': 'fas fa-cog'},
    ]
    
    for category_data in categories:
        category, created = ServiceCategory.objects.get_or_create(
            name=category_data['name'],
            defaults=category_data
        )
        if created:
            print(f"✅ Created category: {category.name}")
        else:
            print(f"ℹ️ Category already exists: {category.name}")

def create_sample_users():
    """Create sample users for testing"""
    # Create customer
    if not User.objects.filter(username='customer1').exists():
        customer_user = User.objects.create_user(
            username='customer1',
            email='customer@example.com',
            password='customer123',
            first_name='John',
            last_name='Doe',
            user_type='customer',
            phone_number='+1234567890',
            address='123 Main St, City, State',
            latitude=40.7128,
            longitude=-74.0060
        )
        CustomerProfile.objects.create(user=customer_user)
        print("✅ Created sample customer: customer1/customer123")
    
    # Create service provider
    if not User.objects.filter(username='provider1').exists():
        provider_user = User.objects.create_user(
            username='provider1',
            email='provider@example.com',
            password='provider123',
            first_name='Mike',
            last_name='Smith',
            user_type='service_provider',
            phone_number='+1234567891',
            address='456 Service Ave, City, State',
            latitude=40.7589,
            longitude=-73.9851
        )
        ServiceProviderProfile.objects.create(
            user=provider_user,
            business_name='Mike\'s Auto Repair',
            business_license='BL123456',
            provider_type='mechanic',
            description='Professional auto repair services with 10+ years experience',
            is_approved=True
        )
        print("✅ Created sample provider: provider1/provider123")

if __name__ == '__main__':
    print("🚀 Setting up Vehicle Service Platform...")
    create_superuser()
    create_service_categories()
    create_sample_users()
    print("✅ Setup complete!")
    print("\n📋 Login Credentials:")
    print("Admin: admin/admin123")
    print("Customer: customer1/customer123")
    print("Provider: provider1/provider123")