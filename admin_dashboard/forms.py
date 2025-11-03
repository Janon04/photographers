from django import forms
from django.contrib.auth import get_user_model
from .models import SystemNotification, PlatformSettings
from bookings.models import Booking

User = get_user_model()

class UserEditForm(forms.ModelForm):
    """Form for editing user details by admin"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'username', 'role',
            'is_verified', 'is_active', 'bio', 'location', 'contact_info',
            'price', 'badges', 'certifications', 'awards', 'social_proof'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_info': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'badges': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated badges'}),
            'certifications': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated certifications'}),
            'awards': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated awards'}),
            'social_proof': forms.URLInput(attrs={'class': 'form-control'}),
        }

class SystemNotificationForm(forms.ModelForm):
    """Form for creating system notifications with email support"""
    
    class Meta:
        model = SystemNotification
        fields = [
            'title', 'message', 'notification_type', 'target_users',
            'delivery_method', 'email_subject', 'send_immediately',
            'is_active', 'expires_at'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter notification title...'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5,
                'placeholder': 'Enter notification message...'
            }),
            'notification_type': forms.Select(attrs={'class': 'form-control'}),
            'target_users': forms.Select(attrs={'class': 'form-control'}),
            'delivery_method': forms.Select(attrs={'class': 'form-control'}),
            'email_subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Custom email subject (optional - defaults to notification title)'
            }),
            'send_immediately': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'expires_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text
        self.fields['delivery_method'].help_text = 'Choose how to deliver this notification'
        self.fields['email_subject'].help_text = 'Leave blank to use notification title as email subject'
        self.fields['send_immediately'].help_text = 'Uncheck to save as draft for later sending'
        self.fields['expires_at'].help_text = 'Optional expiration date for the notification'
        
        # Make email_subject conditional
        self.fields['email_subject'].required = False

class PlatformSettingsForm(forms.ModelForm):
    """Form for managing platform settings"""
    
    class Meta:
        model = PlatformSettings
        fields = ['key', 'value', 'description']
        widgets = {
            'key': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }

class BookingSearchForm(forms.Form):
    """Form for searching and filtering bookings"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by client, photographer, service, or location...'
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + list(Booking.STATUS_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    payment_status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Payment Statuses')] + list(Booking.PAYMENT_STATUS_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

class UserSearchForm(forms.Form):
    """Form for searching and filtering users"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by email, name, or username...'
        })
    )
    role = forms.ChoiceField(
        required=False,
        choices=[('', 'All Roles')] + list(User.Roles.choices),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    verified = forms.ChoiceField(
        required=False,
        choices=[('', 'All'), ('true', 'Verified'), ('false', 'Unverified')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    active = forms.ChoiceField(
        required=False,
        choices=[('', 'All'), ('true', 'Active'), ('false', 'Inactive')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class ReviewSearchForm(forms.Form):
    """Form for searching and filtering reviews"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by reviewer, photographer, or comment...'
        })
    )
    approved = forms.ChoiceField(
        required=False,
        choices=[('', 'All'), ('true', 'Approved'), ('false', 'Pending Approval')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    rating = forms.ChoiceField(
        required=False,
        choices=[('', 'All Ratings')] + [(str(i), f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)],
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class SubscriptionPlanForm(forms.ModelForm):
    """Form for creating and editing subscription plans"""
    
    class Meta:
        from payments.models import SubscriptionPlan
        model = SubscriptionPlan
        fields = [
            'name', 'display_name', 'price_monthly', 'price_yearly', 'currency',
            'features_description', 'support_level', 'customization_level',
            'max_photos_upload', 'max_storage_gb', 'max_bookings_per_month',
            'max_portfolio_items', 'additional_services', 'commission_rate',
            'priority_support', 'analytics_access', 'api_access',
            'includes_premium_support', 'includes_consulting', 'includes_add_ons',
            'is_active'
        ]
        widgets = {
            'name': forms.Select(attrs={'class': 'form-control'}),
            'display_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Basic Plan'}),
            'price_monthly': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'price_yearly': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'currency': forms.TextInput(attrs={'class': 'form-control', 'value': 'RWF', 'readonly': True}),
            'features_description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5, 
                'placeholder': 'Enter features, one per line...'
            }),
            'support_level': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Email Support'}),
            'customization_level': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Basic Templates'}),
            'max_photos_upload': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '-1',
                'placeholder': 'Use -1 for unlimited'
            }),
            'max_storage_gb': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '-1',
                'placeholder': 'Use -1 for unlimited'
            }),
            'max_bookings_per_month': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '-1',
                'placeholder': 'Use -1 for unlimited'
            }),
            'max_portfolio_items': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '-1',
                'placeholder': 'Use -1 for unlimited'
            }),
            'additional_services': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Additional services and benefits...'
            }),
            'commission_rate': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0', 
                'max': '100',
                'placeholder': 'Platform commission percentage'
            }),
            'priority_support': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'analytics_access': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'api_access': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'includes_premium_support': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'includes_consulting': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'includes_add_ons': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Import here to avoid circular imports
        from payments.models import SubscriptionPlan
        
        # Set choices for plan name
        self.fields['name'].widget.choices = SubscriptionPlan.PLAN_CHOICES
        
        # Add help text
        self.fields['max_photos_upload'].help_text = "Maximum photos per month (-1 for unlimited)"
        self.fields['max_storage_gb'].help_text = "Storage limit in GB (-1 for unlimited)"
        self.fields['max_bookings_per_month'].help_text = "Maximum bookings per month (-1 for unlimited)"
        self.fields['max_portfolio_items'].help_text = "Maximum portfolio items (-1 for unlimited)"
        self.fields['commission_rate'].help_text = "Platform commission rate for this plan"