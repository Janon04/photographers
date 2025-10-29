from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from .models import User, Message

class CustomUserCreationForm(UserCreationForm):
	# Custom username field that allows spaces and more characters
	username = forms.CharField(
		max_length=150, 
		required=True, 
		help_text='Required. 150 characters or fewer. Letters, digits, spaces, and common punctuation allowed.',
		validators=[
			RegexValidator(
				regex=r'^[\w\s\.\-\_]+$',
				message='Username can only contain letters, numbers, spaces, dots, hyphens, and underscores.',
				code='invalid_username'
			)
		]
	)
	badges = forms.CharField(max_length=255, required=False, help_text='Badges or special recognitions (comma-separated)')
	certifications = forms.CharField(max_length=255, required=False, help_text='Certifications (comma-separated)')
	awards = forms.CharField(max_length=255, required=False, help_text='Awards (comma-separated)')
	social_proof = forms.URLField(required=False, help_text='Link to social proof (portfolio, Instagram, etc.)')

	class Meta:
		model = User
		fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'bio', 'profile_picture', 'location', 'contact_info', 'is_verified', 'role', 'badges', 'certifications', 'awards', 'social_proof')

	def clean_username(self):
		username = self.cleaned_data['username'].strip()
		
		# Check if username is empty after stripping
		if not username:
			raise forms.ValidationError('Username cannot be empty or contain only spaces.')
		
		# Check for minimum length
		if len(username) < 3:
			raise forms.ValidationError('Username must be at least 3 characters long.')
		
		# Check if username already exists (case-insensitive)
		if User.objects.filter(username__iexact=username).exists():
			raise forms.ValidationError('That username is already taken. Please choose another.')
		
		return username

	def save(self, commit=True):
		user = super().save(commit=False)
		user.username = self.cleaned_data['username']
		if commit:
			user.save()
		return user

class PhotographerSearchForm(forms.Form):
    location = forms.CharField(required=False, label='Location')
    min_price = forms.DecimalField(required=False, min_value=0, label='Min Price')
    max_price = forms.DecimalField(required=False, min_value=0, label='Max Price')
    min_rating = forms.DecimalField(required=False, min_value=0, max_value=5, label='Min Rating')
    role = forms.ChoiceField(
        required=False,
        choices=[('', 'Any'), ('photographer', 'Photographer'), ('client', 'Client')],
        label='Role'
    )

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['receiver', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message...'}),
        }
