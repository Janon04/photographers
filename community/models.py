from django.db import models
from users.models import User
# Reporting model for posts, reviews, and photos
class ContentReport(models.Model):
	REPORT_TYPE_CHOICES = [
		('post', 'Post'),
		('review', 'Review'),
		('photo', 'Photo'),
	]
	report_type = models.CharField(max_length=10, choices=REPORT_TYPE_CHOICES)
	object_id = models.PositiveIntegerField()
	reporter = models.ForeignKey(User, on_delete=models.CASCADE)
	reason = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	is_resolved = models.BooleanField(default=False)

	def __str__(self):
		return f"{self.report_type} #{self.object_id} reported by {self.reporter.email}"

from ckeditor.fields import RichTextField

class CommunityCategory(models.Model):
	name = models.CharField(max_length=100, unique=True)

	def __str__(self):
		return self.name


from PIL import Image

class Post(models.Model):
	title = models.CharField(max_length=255)
	description = models.TextField()
	content = RichTextField()
	date = models.DateTimeField(auto_now_add=True)
	image = models.ImageField(upload_to='community_posts/', blank=True, null=True)
	category = models.ForeignKey(CommunityCategory, on_delete=models.SET_NULL, null=True, related_name='posts')
	is_approved = models.BooleanField(default=False, help_text='Admin must approve before public display.')

	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		if self.image:
			img = Image.open(self.image.path)
			max_size = (800, 800)
			img.thumbnail(max_size, Image.LANCZOS)
			img.save(self.image.path, optimize=True, quality=80)
	def __str__(self):
		return self.title
	from django.db import models
	from users.models import User

	class CommunityPost(models.Model):
		author = models.ForeignKey(User, on_delete=models.CASCADE)
		title = models.CharField(max_length=255)
		content = models.TextField()
		created_at = models.DateTimeField(auto_now_add=True)

		def __str__(self):
			return self.title
