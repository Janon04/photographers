from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from .models import User, Message
from utils.rwanda_locations import get_provinces, get_districts, get_sectors, get_cells, get_villages, format_location

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
	
	# Rwanda Location Fields
	province = forms.ChoiceField(
		choices=[('', 'Select Province')] + [(p, p) for p in get_provinces()],
		required=False,
		help_text='Select your province in Rwanda'
	)
	district = forms.ChoiceField(
		choices=[('', 'Select District')],
		required=False,
		help_text='Select your district'
	)
	sector = forms.ChoiceField(
		choices=[('', 'Select Sector')],
		required=False,
		help_text='Select your sector'
	)
	cell = forms.ChoiceField(
		choices=[('', 'Select Cell')],
		required=False,
		help_text='Select your cell'
	)
	village = forms.ChoiceField(
		choices=[('', 'Select Village')],
		required=False,
		help_text='Select your village'
	)
	
	badges = forms.CharField(max_length=255, required=False, help_text='Badges or special recognitions (comma-separated)')
	certifications = forms.CharField(max_length=255, required=False, help_text='Certifications (comma-separated)')
	awards = forms.CharField(max_length=255, required=False, help_text='Awards (comma-separated)')
	social_proof = forms.URLField(required=False, help_text='Link to social proof (portfolio, Instagram, etc.)')

	class Meta:
		model = User
		fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'bio', 'profile_picture', 'location', 'contact_info', 'is_verified', 'role', 'badges', 'certifications', 'awards', 'social_proof')

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		# Update district choices if province is selected
		if 'province' in self.data:
			try:
				province = self.data.get('province')
				self.fields['district'].choices = [('', 'Select District')] + [(d, d) for d in get_districts(province)]
			except (ValueError, TypeError):
				pass
		
		# Update sector choices if district is selected
		if 'district' in self.data:
			try:
				province = self.data.get('province')
				district = self.data.get('district')
				self.fields['sector'].choices = [('', 'Select Sector')] + [(s, s) for s in get_sectors(province, district)]
			except (ValueError, TypeError):
				pass
		
		# Update cell choices if sector is selected
		if 'sector' in self.data:
			try:
				province = self.data.get('province')
				district = self.data.get('district')
				sector = self.data.get('sector')
				self.fields['cell'].choices = [('', 'Select Cell')] + [(c, c) for c in get_cells(province, district, sector)]
			except (ValueError, TypeError):
				pass
		
		# Update village choices if cell is selected
		if 'cell' in self.data:
			try:
				province = self.data.get('province')
				district = self.data.get('district')
				sector = self.data.get('sector')
				cell = self.data.get('cell')
				self.fields['village'].choices = [('', 'Select Village')] + [(v, v) for v in get_villages(province, district, sector, cell)]
			except (ValueError, TypeError):
				pass

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
		
		# Format and save location
		province = self.cleaned_data.get('province')
		district = self.cleaned_data.get('district')
		sector = self.cleaned_data.get('sector')
		cell = self.cleaned_data.get('cell')
		village = self.cleaned_data.get('village')
		
		user.location = format_location(province, district, sector, cell, village)
		
		if commit:
			user.save()
		return user

class PhotographerSearchForm(forms.Form):
    location = forms.CharField(required=False, label='Location (search any part)')
    province = forms.ChoiceField(
        choices=[('', 'Any Province')] + [(p, p) for p in get_provinces()],
        required=False,
        label='Province'
    )
    district = forms.CharField(required=False, label='District')
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


class ProfileForm(forms.ModelForm):
	"""Form for editing user profile (used by edit_profile view)."""
	province = forms.ChoiceField(
		choices=[('', 'Select Province')] + [(p, p) for p in get_provinces()],
		required=False
	)
	district = forms.ChoiceField(choices=[('', 'Select District')], required=False)
	sector = forms.ChoiceField(choices=[('', 'Select Sector')], required=False)
	cell = forms.ChoiceField(choices=[('', 'Select Cell')], required=False)
	village = forms.ChoiceField(choices=[('', 'Select Village')], required=False)

	class Meta:
		model = User
		fields = ('username', 'email', 'first_name', 'last_name', 'bio', 'profile_picture', 'contact_info', 'social_proof')

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# Pre-fill location choices if instance has a formatted location
		# Note: editing full location is optional; user can leave blank
		if 'province' in self.data:
			try:
				province = self.data.get('province')
				self.fields['district'].choices = [('', 'Select District')] + [(d, d) for d in get_districts(province)]
			except Exception:
				pass
		elif self.instance and self.instance.location:
			# No structured location stored; skip
			pass

	def save(self, commit=True):
		user = super().save(commit=False)
		# Format and save location if provided
		province = self.cleaned_data.get('province')
		district = self.cleaned_data.get('district')
		sector = self.cleaned_data.get('sector')
		cell = self.cleaned_data.get('cell')
		village = self.cleaned_data.get('village')
		if province or district or sector or cell or village:
			user.location = format_location(province, district, sector, cell, village)
		if commit:
			user.save()
		return user
