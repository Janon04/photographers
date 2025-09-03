

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.crypto import get_random_string
from .models import User
from .forms import CustomUserCreationForm

@admin.register(User)
class UserAdmin(BaseUserAdmin):
	add_form = CustomUserCreationForm
	fieldsets = (
		(None, {'fields': ('email', 'first_name', 'last_name', 'password')}),
		('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
		('Important dates', {'fields': ('last_login', 'date_joined')}),
		('Additional Info', {
			'fields': ('bio', 'profile_picture', 'location', 'contact_info', 'is_verified', 'role'),
		}),
	)
	add_fieldsets = (
		(None, {
			'classes': ('wide',),
			'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'bio', 'profile_picture', 'location', 'contact_info', 'is_verified', 'role'),
		}),
	)
	list_display = ('email', 'first_name', 'last_name', 'role', 'is_verified', 'is_staff')
	search_fields = ('email', 'first_name', 'last_name', 'role')
	ordering = ('email',)
	readonly_fields = ('username',)

	def save_model(self, request, obj, form, change):
		# Auto-generate username if not set
		if not obj.username:
			base = (obj.first_name + obj.last_name).lower().replace(' ', '')
			if not base:
				base = 'user'
			obj.username = base + get_random_string(5)
		super().save_model(request, obj, form, change)
