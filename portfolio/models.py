from PIL import Image


from django.db import models
from users.models import User
from django.utils import timezone

class Category(models.Model):
	name = models.CharField(max_length=100, unique=True)

	def __str__(self):
		return self.name


class Photo(models.Model):
	photographer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
	image = models.ImageField(upload_to='portfolio_photos/')
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='photos')
	uploaded_at = models.DateTimeField(default=timezone.now)
	is_approved = models.BooleanField(default=False, help_text='Admin must approve before public display.')

	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		if self.image:
			img = Image.open(self.image.path)
			max_size = (1280, 1280)
			img.thumbnail(max_size, Image.LANCZOS)
			img.save(self.image.path, optimize=True, quality=80)
	def __str__(self):
		return f"{self.title} by {self.photographer.email}"

	class Meta:
		ordering = ['-uploaded_at']


# Story model for photographers
from datetime import timedelta
class Story(models.Model):
	photographer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
	image = models.ImageField(upload_to='stories/')
	created_at = models.DateTimeField(auto_now_add=True)

	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		if self.image:
			img = Image.open(self.image.path)
			max_size = (800, 800)
			img.thumbnail(max_size, Image.LANCZOS)
			img.save(self.image.path, optimize=True, quality=80)
	def is_active(self):
		from django.utils import timezone
		return self.created_at >= timezone.now() - timedelta(hours=24)

	def __str__(self):
		return f"Story by {self.photographer.username} at {self.created_at}"
	
	# Upcoming Event model for photographers
class Event(models.Model):
	photographer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
	title = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	date = models.DateField()
	location = models.CharField(max_length=255)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.title} by {self.photographer.get_full_name()} on {self.date}"
