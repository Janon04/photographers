
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
	class Roles(models.TextChoices):
		PHOTOGRAPHER = 'photographer', _('Photographer')
		CLIENT = 'client', _('Client')

	email = models.EmailField(_('email address'), unique=True)
	bio = models.TextField(_('bio'), blank=True)
	profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
	location = models.CharField(max_length=255, blank=True)
	contact_info = models.CharField(max_length=255, blank=True)
	is_verified = models.BooleanField(default=False)
	role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.CLIENT)

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['username']

	def __str__(self):
		if self.role == self.Roles.PHOTOGRAPHER:
			full_name = f"{self.first_name} {self.last_name}".strip()
			return full_name if full_name else self.username
		return self.email
