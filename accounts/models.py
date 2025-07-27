from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class User(AbstractUser):
    USER_TYPES = (
        ('customer', 'Customer'),
        ('service_provider', 'Service Provider'),
        ('admin', 'Admin'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='customer')
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')],
        blank=True
    )
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    emergency_contact = models.CharField(max_length=15, blank=True)
    preferred_payment_method = models.CharField(
        max_length=20,
        choices=[('cash', 'Cash'), ('online', 'Online')],
        default='cash'
    )
    
    def __str__(self):
        return f"Customer: {self.user.username}"

class Vehicle(models.Model):
    VEHICLE_TYPES = (
        ('car', 'Car'),
        ('motorcycle', 'Motorcycle'),
        ('truck', 'Truck'),
        ('bus', 'Bus'),
        ('other', 'Other'),
    )
    
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='vehicles')
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    license_plate = models.CharField(max_length=20, unique=True)
    color = models.CharField(max_length=30, blank=True)
    is_primary = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.year} {self.make} {self.model} ({self.license_plate})"

class ServiceProviderProfile(models.Model):
    PROVIDER_TYPES = (
        ('mechanic', 'Mechanic'),
        ('fuel_station', 'Fuel Station'),
        ('towing_service', 'Towing Service'),
        ('car_wash', 'Car Wash'),
        ('parts_dealer', 'Parts Dealer'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='service_provider_profile')
    business_name = models.CharField(max_length=100)
    business_license = models.CharField(max_length=50, unique=True)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES)
    description = models.TextField(blank=True)
    operating_hours = models.CharField(max_length=100, blank=True)
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    unpaid_dues_count = models.IntegerField(default=0)
    total_unpaid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.business_name} ({self.get_provider_type_display()})"
    
    @property
    def is_eligible_for_requests(self):
        return self.is_approved and self.is_active and self.unpaid_dues_count < 5