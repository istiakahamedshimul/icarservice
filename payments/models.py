from django.db import models
from django.utils import timezone
from accounts.models import ServiceProviderProfile, CustomerProfile
from bookings.models import ServiceRequest

class Invoice(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('online', 'Online'),
        ('card', 'Card'),
    )
    
    service_request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=20, unique=True)
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment details
    payment_status = models.CharField(max_length=15, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Dates
    issued_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Additional details
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.service_request}"
    
    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount
    
    def generate_invoice_number(self):
        if not self.invoice_number:
            today = timezone.now().date()
            count = Invoice.objects.filter(issued_at__date=today).count() + 1
            self.invoice_number = f"INV-{today.strftime('%Y%m%d')}-{count:04d}"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1.00)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.description} - {self.invoice.invoice_number}"

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=Invoice.PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Payment gateway details
    transaction_id = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Payment {self.id} - {self.invoice.invoice_number} - ${self.amount}"

class Commission(models.Model):
    COMMISSION_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    )
    
    service_provider = models.ForeignKey(ServiceProviderProfile, on_delete=models.CASCADE, related_name='commissions')
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='commission')
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=COMMISSION_STATUS_CHOICES, default='pending')
    
    # For cash payments
    is_cash_payment = models.BooleanField(default=False)
    due_date = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Commission for {self.service_provider.business_name} - ${self.commission_amount}"
    
    def mark_as_overdue(self):
        if self.status == 'pending' and timezone.now() > self.due_date:
            self.status = 'overdue'
            self.save()
            
            # Update service provider's unpaid dues count
            self.service_provider.unpaid_dues_count += 1
            self.service_provider.total_unpaid_amount += self.commission_amount
            self.service_provider.save()