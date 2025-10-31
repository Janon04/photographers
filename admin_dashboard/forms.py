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