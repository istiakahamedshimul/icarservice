from django.db import models
from accounts.models import ServiceProviderProfile

class ServiceCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # Font Awesome icon class
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Service Categories"
    
    def __str__(self):
        return self.name

class Service(models.Model):
    provider = models.ForeignKey(ServiceProviderProfile, on_delete=models.CASCADE, related_name='services')
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_duration = models.DurationField(help_text="Estimated time to complete service")
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.provider.business_name}"

class ServiceArea(models.Model):
    provider = models.ForeignKey(ServiceProviderProfile, on_delete=models.CASCADE, related_name='service_areas')
    area_name = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    radius_km = models.DecimalField(max_digits=6, decimal_places=2, default=5.0)
    
    def __str__(self):
        return f"{self.provider.business_name} - {self.area_name}"