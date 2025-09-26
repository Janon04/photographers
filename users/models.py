from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from PIL import Image

class User(AbstractUser):
	class Roles(models.TextChoices):
		PHOTOGRAPHER = 'photographer', _('Photographer')
		CLIENT = 'client', _('Client')

	email = models.EmailField(_('email address'), unique=True, blank=False, null=False, help_text=_('Required. Enter a valid email address.'))
	bio = models.TextField(_('bio'), blank=True)
	profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
	location = models.CharField(max_length=255, blank=True)
	contact_info = models.CharField(max_length=255, blank=True)
	is_verified = models.BooleanField(default=False)
	role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.CLIENT)
	price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text=_('Typical session price (optional)'))
	# Photographer profile enhancements
	badges = models.CharField(max_length=255, blank=True, help_text=_('Badges or special recognitions (comma-separated)'))
	certifications = models.CharField(max_length=255, blank=True, help_text=_('Certifications (comma-separated)'))
	awards = models.CharField(max_length=255, blank=True, help_text=_('Awards (comma-separated)'))
	social_proof = models.URLField(blank=True, help_text=_('Link to social proof (portfolio, Instagram, etc.)'))

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['username']

	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		if self.profile_picture:
			img = Image.open(self.profile_picture.path)
			max_size = (400, 400)
			img.thumbnail(max_size, Image.LANCZOS)
			img.save(self.profile_picture.path, optimize=True, quality=80)

	@property
	def average_rating(self):
		if self.role != self.Roles.PHOTOGRAPHER:
			return None
		reviews = self.reviews_received.filter(is_approved=True)
		if reviews.exists():
			return round(sum(r.rating for r in reviews) / reviews.count(), 2)
		return None
	def __str__(self):
		if self.role == self.Roles.PHOTOGRAPHER:
			full_name = f"{self.first_name} {self.last_name}".strip()
			return full_name if full_name else self.username
		return self.email

class Message(models.Model):
    sender = models.ForeignKey('User', related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey('User', related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender} to {self.receiver} at {self.timestamp}"
