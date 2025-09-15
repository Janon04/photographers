
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
	username = forms.CharField(max_length=150, required=True, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.')

	class Meta:
		model = User
		fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'bio', 'profile_picture', 'location', 'contact_info', 'is_verified', 'role')

	def clean_username(self):
		username = self.cleaned_data['username']
		if User.objects.filter(username=username).exists():
			raise forms.ValidationError('That username is already taken. Please choose another.')
		return username

	def save(self, commit=True):
		user = super().save(commit=False)
		user.username = self.cleaned_data['username']
		if commit:
			user.save()
		return user
