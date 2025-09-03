
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
	class Meta:
		model = User
		fields = ('email', 'first_name', 'last_name', 'password1', 'password2', 'bio', 'profile_picture', 'location', 'contact_info', 'is_verified', 'role')

	def save(self, commit=True):
		user = super().save(commit=False)
		# Auto-generate username
		base = (user.first_name + user.last_name).lower().replace(' ', '')
		if not base:
			base = 'user'
		from django.utils.crypto import get_random_string
		user.username = base + get_random_string(5)
		if commit:
			user.save()
		return user
