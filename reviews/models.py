from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import CustomerProfile, ServiceProviderProfile
from bookings.models import ServiceRequest

class Review(models.Model):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='reviews_given')
    service_provider = models.ForeignKey(ServiceProviderProfile, on_delete=models.CASCADE, related_name='reviews_received')
    service_request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE, related_name='review')
    
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    
    # Review aspects
    quality_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    timeliness_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    professionalism_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    value_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    
    is_featured = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review by {self.customer.user.username} for {self.service_provider.business_name} - {self.rating}★"

class ReviewResponse(models.Model):
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name='response')
    response_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Response to review {self.review.id}"