
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import datetime, timedelta
from users.models import User
from bookings.models import Booking


class SubscriptionPlan(models.Model):
    """Subscription plans for photographers"""
    PLAN_CHOICES = [
        ('basic', 'Basic Plan'),
        ('standard', 'Standard Plan'),
        ('premium', 'Premium Plan'),
    ]
    
    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    display_name = models.CharField(max_length=50)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='RWF')
    
    # Features
    features_description = models.TextField()
    support_level = models.CharField(max_length=50)
    customization_level = models.CharField(max_length=50)
    
    # Usage Limits
    max_photos_upload = models.IntegerField(help_text="Maximum photos per month (-1 for unlimited)")
    max_storage_gb = models.IntegerField(help_text="Storage limit in GB (-1 for unlimited)")
    max_bookings_per_month = models.IntegerField(help_text="Maximum bookings per month (-1 for unlimited)")
    max_portfolio_items = models.IntegerField(help_text="Maximum portfolio items (-1 for unlimited)")
    
    # Additional Services
    additional_services = models.TextField()
    includes_premium_support = models.BooleanField(default=False)
    includes_consulting = models.BooleanField(default=False)
    includes_add_ons = models.BooleanField(default=False)
    
    # Platform Settings
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.00,
        help_text="Platform commission rate for this plan"
    )
    priority_support = models.BooleanField(default=False)
    analytics_access = models.BooleanField(default=False)
    api_access = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['price_monthly']
    
    def __str__(self):
        return f"{self.display_name} - {self.price_monthly} {self.currency}/month"
    
    def get_yearly_price(self):
        """Calculate yearly price with discount if not set"""
        if self.price_yearly:
            return self.price_yearly
        return self.price_monthly * 10  # 2 months free discount
    
    def get_features_list(self):
        """Return features as a list"""
        return [f.strip() for f in self.features_description.split('\n') if f.strip()]
    
    def is_unlimited_storage(self):
        return self.max_storage_gb == -1
    
    def is_unlimited_photos(self):
        return self.max_photos_upload == -1


class UserSubscription(models.Model):
    """User subscription tracking"""
    BILLING_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('trial', 'Trial'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CHOICES, default='monthly')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    
    # Subscription dates
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    trial_end_date = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Usage tracking
    photos_uploaded_this_month = models.IntegerField(default=0)
    storage_used_gb = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bookings_this_month = models.IntegerField(default=0)
    portfolio_items_count = models.IntegerField(default=0)
    
    # Payment tracking
    auto_renew = models.BooleanField(default=True)
    next_billing_date = models.DateTimeField()
    last_payment_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.display_name} ({self.status})"
    
    def save(self, *args, **kwargs):
        if not self.end_date:
            if self.billing_cycle == 'yearly':
                self.end_date = self.start_date + timedelta(days=365)
                self.next_billing_date = self.end_date
            else:
                self.end_date = self.start_date + timedelta(days=30)
                self.next_billing_date = self.end_date
        
        # Set trial end date for new subscriptions
        if not self.trial_end_date and self.status == 'trial':
            self.trial_end_date = self.start_date + timedelta(days=14)  # 14-day trial
        
        super().save(*args, **kwargs)
    
    def is_active(self):
        return self.status in ['active', 'trial'] and timezone.now() < self.end_date
    
    def is_trial(self):
        return self.status == 'trial' and self.trial_end_date and timezone.now() < self.trial_end_date
    
    def days_until_expiry(self):
        if self.end_date:
            delta = self.end_date - timezone.now()
            return max(0, delta.days)
        return 0
    
    def get_monthly_price(self):
        if self.billing_cycle == 'yearly':
            return self.plan.get_yearly_price()
        return self.plan.price_monthly
    
    def can_upload_photos(self, count=1):
        if self.plan.is_unlimited_photos():
            return True
        return (self.photos_uploaded_this_month + count) <= self.plan.max_photos_upload
    
    def can_add_storage(self, gb):
        if self.plan.is_unlimited_storage():
            return True
        return (self.storage_used_gb + gb) <= self.plan.max_storage_gb
    
    def can_create_booking(self):
        if self.plan.max_bookings_per_month == -1:
            return True
        return self.bookings_this_month < self.plan.max_bookings_per_month
    
    def reset_monthly_usage(self):
        """Reset monthly usage counters"""
        self.photos_uploaded_this_month = 0
        self.bookings_this_month = 0
        self.save()


class SubscriptionPayment(models.Model):
    """Track subscription payments"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='RWF')
    billing_period_start = models.DateTimeField()
    billing_period_end = models.DateTimeField()
    
    payment_method = models.CharField(max_length=50)
    payment_gateway = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    gateway_transaction_id = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Payment Method Specific Details
    # For Card Payments
    card_last_four = models.CharField(max_length=4, blank=True, help_text="Last 4 digits of card")
    card_brand = models.CharField(max_length=20, blank=True, help_text="Visa, Mastercard, Amex, etc.")
    cardholder_name = models.CharField(max_length=100, blank=True)
    
    # For Mobile Money
    mobile_money_provider = models.CharField(max_length=20, blank=True, help_text="MTN, Airtel, etc.")
    mobile_money_phone = models.CharField(max_length=20, blank=True)
    
    # For PayPal
    paypal_email = models.EmailField(blank=True)
    paypal_payer_id = models.CharField(max_length=100, blank=True)
    
    # Invoice details
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    invoice_url = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.invoice_number} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class PaymentGateway(models.Model):
    """Payment gateway configuration"""
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    supports_escrow = models.BooleanField(default=False)
    processing_fee_percentage = models.DecimalField(max_digits=5, decimal_places=4, default=0.029)  # 2.9%
    fixed_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.30)
    currency = models.CharField(max_length=3, default='RWF')
    
    def __str__(self):
        return self.name


class PlatformCommission(models.Model):
    """Platform commission settings"""
    commission_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.00,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Platform commission percentage (0-50%)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Commission: {self.commission_percentage}%"
    
    @classmethod
    def get_current_rate(cls):
        """Get the current active commission rate"""
        current = cls.objects.filter(is_active=True).first()
        return current.commission_percentage if current else Decimal('10.00')


class Transaction(models.Model):
    """Enhanced transaction model with escrow and commission tracking"""
    
    class TransactionType(models.TextChoices):
        CLIENT_PAYMENT = 'client_payment', 'Client Payment'
        PHOTOGRAPHER_PAYOUT = 'photographer_payout', 'Photographer Payout'
        PLATFORM_FEE = 'platform_fee', 'Platform Fee'
        REFUND = 'refund', 'Refund'
        COMMISSION = 'commission', 'Commission'
    
    class TransactionStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'
        REFUNDED = 'refunded', 'Refunded'
        HELD_ESCROW = 'held_escrow', 'Held in Escrow'
    
    # Core fields
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='transactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices, default=TransactionType.CLIENT_PAYMENT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='RWF')
    status = models.CharField(max_length=20, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    
    # Payment processing
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.PROTECT, null=True, blank=True)
    external_transaction_id = models.CharField(max_length=200, blank=True)
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Commission tracking
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Amount after fees and commission")
    
    # Escrow
    escrow_released_at = models.DateTimeField(null=True, blank=True)
    escrow_release_reason = models.CharField(max_length=100, blank=True)
    
    # Metadata
    payment_method = models.CharField(max_length=50, default='Stripe')
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Payment Method Specific Details
    # For Card Payments
    card_last_four = models.CharField(max_length=4, blank=True, help_text="Last 4 digits of card")
    card_brand = models.CharField(max_length=20, blank=True, help_text="Visa, Mastercard, Amex, etc.")
    cardholder_name = models.CharField(max_length=100, blank=True)
    
    # For Mobile Money
    mobile_money_provider = models.CharField(max_length=20, blank=True, help_text="MTN, Airtel, etc.")
    mobile_money_phone = models.CharField(max_length=20, blank=True)
    
    # For PayPal
    paypal_email = models.EmailField(blank=True)
    paypal_payer_id = models.CharField(max_length=100, blank=True)
    
    # For Bank Transfer
    bank_reference = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'transaction_type']),
            models.Index(fields=['booking', 'transaction_type']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} {self.currency} ({self.status})"
    
    def calculate_commission_and_fees(self):
        """Calculate commission and processing fees"""
        if self.transaction_type == self.TransactionType.CLIENT_PAYMENT:
            # Calculate platform commission
            commission_rate = PlatformCommission.get_current_rate()
            self.commission_rate = commission_rate
            self.commission_amount = (self.amount * commission_rate / 100).quantize(Decimal('0.01'))
            
            # Calculate processing fee
            if self.gateway:
                fee_percentage = self.gateway.processing_fee_percentage * 100  # Convert to percentage
                self.processing_fee = (
                    (self.amount * fee_percentage / 100) + self.gateway.fixed_fee
                ).quantize(Decimal('0.01'))
            
            # Calculate net amount for photographer
            self.net_amount = self.amount - self.commission_amount - self.processing_fee
        
        self.save()
    
    def release_escrow(self, reason="Service completed"):
        """Release funds from escrow to photographer"""
        if self.status == self.TransactionStatus.HELD_ESCROW:
            self.status = self.TransactionStatus.COMPLETED
            self.escrow_released_at = timezone.now()
            self.escrow_release_reason = reason
            self.completed_at = timezone.now()
            self.save()
            
            # Create photographer payout transaction
            PhotographerPayout.objects.create(
                transaction=self,
                photographer=self.booking.photographer,
                amount=self.net_amount,
                status='pending'
            )


class PhotographerPayout(models.Model):
    """Track payouts to photographers"""
    
    class PayoutStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
    
    class PayoutMethod(models.TextChoices):
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
        MOBILE_MONEY = 'mobile_money', 'Mobile Money'
        PAYPAL = 'paypal', 'PayPal'
        STRIPE = 'stripe', 'Stripe Transfer'
    
    payout_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='payout')
    photographer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payouts')
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='RWF')
    status = models.CharField(max_length=20, choices=PayoutStatus.choices, default=PayoutStatus.PENDING)
    method = models.CharField(max_length=20, choices=PayoutMethod.choices, default=PayoutMethod.BANK_TRANSFER)
    
    # Bank/Mobile details (encrypted in production)
    recipient_account = models.CharField(max_length=100, blank=True)
    recipient_name = models.CharField(max_length=100, blank=True)
    
    # Processing
    external_payout_id = models.CharField(max_length=200, blank=True)
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payout {self.payout_id} - {self.amount} {self.currency} to {self.photographer.get_full_name()}"


class PlatformRevenue(models.Model):
    """Track platform revenue from commissions"""
    date = models.DateField(unique=True)
    total_commission = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_processing_fees = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_transactions = models.PositiveIntegerField(default=0)
    net_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Revenue {self.date} - {self.net_revenue} RWF"
    
    @classmethod
    def calculate_daily_revenue(cls, date=None):
        """Calculate and store daily revenue"""
        if not date:
            date = timezone.now().date()
        
        # Get all completed commission transactions for the date
        transactions = Transaction.objects.filter(
            transaction_type=Transaction.TransactionType.CLIENT_PAYMENT,
            status=Transaction.TransactionStatus.COMPLETED,
            completed_at__date=date
        )
        
        total_commission = sum(t.commission_amount for t in transactions)
        total_processing_fees = sum(t.processing_fee for t in transactions)
        total_count = transactions.count()
        net_revenue = total_commission  # Platform keeps commission, processing fees go to gateway
        
        revenue, created = cls.objects.get_or_create(
            date=date,
            defaults={
                'total_commission': total_commission,
                'total_processing_fees': total_processing_fees,
                'total_transactions': total_count,
                'net_revenue': net_revenue
            }
        )
        
        if not created:
            revenue.total_commission = total_commission
            revenue.total_processing_fees = total_processing_fees
            revenue.total_transactions = total_count
            revenue.net_revenue = net_revenue
            revenue.save()
        
        return revenue
