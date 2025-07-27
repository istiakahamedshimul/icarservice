from django.db import models
from django.utils import timezone
from accounts.models import CustomerProfile, ServiceProviderProfile, Vehicle
from services.models import Service

class ServiceRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('emergency', 'Emergency'),
    )
    
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='service_requests')
    service_provider = models.ForeignKey(ServiceProviderProfile, on_delete=models.CASCADE, related_name='received_requests', null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    # Location details
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    pickup_address = models.TextField()
    
    # Timing
    requested_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    
    # Pricing
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Additional info
    notes = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Request #{self.id} - {self.service.name} ({self.status})"
    
    def update_status(self, new_status, user=None):
        self.status = new_status
        if new_status == 'accepted':
            self.accepted_at = timezone.now()
        elif new_status == 'in_progress':
            self.started_at = timezone.now()
        elif new_status == 'completed':
            self.completed_at = timezone.now()
        self.save()

class ServiceRequestUpdate(models.Model):
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='updates')
    status = models.CharField(max_length=15, choices=ServiceRequest.STATUS_CHOICES)
    message = models.TextField(blank=True)
    created_by = models.CharField(max_length=20)  # 'customer' or 'provider'
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Update for Request #{self.service_request.id} - {self.status}"