from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class AdminActivityLog(models.Model):
    """Track admin activities for audit purposes"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('suspend', 'Suspend'),
        ('activate', 'Activate'),
    ]
    
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_activities')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    target_model = models.CharField(max_length=100)  # Model name
    target_id = models.PositiveIntegerField()  # Object ID
    target_description = models.CharField(max_length=255)  # Human readable description
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.admin_user.username} {self.action} {self.target_model} at {self.timestamp}"

class PlatformSettings(models.Model):
    """Platform-wide settings manageable by admins"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=255)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Platform Setting"
        verbose_name_plural = "Platform Settings"
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}..."

class SystemNotification(models.Model):
    """System-wide notifications from admins to users"""
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('maintenance', 'Maintenance'),
        ('feature', 'New Feature'),
        ('promotion', 'Promotion'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    target_users = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All Users'),
            ('photographers', 'Photographers Only'),
            ('clients', 'Clients Only'),
        ],
        default='all'
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.notification_type})"

class PlatformAnalytics(models.Model):
    """Daily analytics snapshot for dashboard"""
    date = models.DateField(unique=True)
    total_users = models.PositiveIntegerField(default=0)
    total_photographers = models.PositiveIntegerField(default=0)
    total_clients = models.PositiveIntegerField(default=0)
    total_bookings = models.PositiveIntegerField(default=0)
    completed_bookings = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    new_registrations = models.PositiveIntegerField(default=0)
    active_photographers = models.PositiveIntegerField(default=0)
    active_clients = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        
    def __str__(self):
        return f"Analytics for {self.date}"
