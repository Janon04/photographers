
# Like/dislike model for photos
from django.db import models
from django.conf import settings
from users.models import User
from django.utils import timezone
from PIL import Image
import json
# Removed import of PhotoComment to resolve circular import

class PhotoLike(models.Model):
	photo = models.ForeignKey('Photo', on_delete=models.CASCADE, related_name='likes')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
	session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
	is_like = models.BooleanField(default=True)  # True=like, False=dislike
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('photo', 'user', 'session_key')

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
	share_count = models.PositiveIntegerField(default=0)

	def save(self, *args, **kwargs):
		# Standard image optimization
		super().save(*args, **kwargs)
		if self.image:
			# Keep higher resolution for better display on high-DPI displays
			# Increase max_size and quality for HD rendering. This affects future uploads.
			img = Image.open(self.image.path)
			
			# Check original image quality
			original_size = img.size
			max_dimension = max(original_size)
			
			# Warn if uploaded image is too small for HD display
			if max_dimension < 1200:
				import warnings
				warnings.warn(
					f"Photo '{self.title}' uploaded with low resolution: {original_size[0]}x{original_size[1]}. "
					f"For best HD quality, upload images at least 1920x1080 or higher.",
					UserWarning
				)
			
			# Convert to RGB if necessary
			if img.mode in ('RGBA', 'LA', 'P'):
				img = img.convert('RGB')
			
			max_size = (2560, 2560)
			img.thumbnail(max_size, Image.LANCZOS)
			# Save at higher quality; balance file size vs fidelity
			img.save(self.image.path, optimize=True, quality=92)
	
	def simulate_ai_analysis(self):
		"""Simulate AI analysis for demo purposes"""
		filename = self.image.name.lower()
		title = self.title.lower()
		description = self.description.lower()
		
		# Simple categorization
		if any(word in filename + title + description for word in ['wedding', 'bride', 'groom']):
			return {'category': 'wedding', 'confidence': 92, 'tags': ['wedding', 'ceremony', 'professional']}
		elif any(word in filename + title + description for word in ['portrait', 'headshot']):
			return {'category': 'portrait', 'confidence': 88, 'tags': ['portrait', 'professional', 'headshot']}
		elif any(word in filename + title + description for word in ['event', 'corporate']):
			return {'category': 'event', 'confidence': 85, 'tags': ['event', 'corporate', 'photography']}
		else:
			return {'category': 'general', 'confidence': 75, 'tags': ['photography', 'professional']}
	
	def get_ai_recommendations(self):
		"""Get AI recommendations for this photo"""
		analysis = self.simulate_ai_analysis()
		return [
			f"Perfect for {analysis['category']} portfolio section",
			"Consider adding more descriptive keywords",
			"Optimize image title for SEO"
		]
	
	def get_suggested_improvements(self):
		"""Get AI-suggested improvements"""
		return [
			"Add more detailed description",
			"Include location information",
			"Consider adding watermark for protection"
		]
	def __str__(self):
		return f"{self.title} by {self.photographer.email}"

	@property
	def likes_count(self):
		return self.likes.filter(is_like=True).count()

	@property
	def dislikes_count(self):
		return self.likes.filter(is_like=False).count()

	@property
	def comments_count(self):
		return self.comments.count()

	def get_user_vote(self, user):
		"""Get user's vote on this photo (like/dislike/none)"""
		if not user.is_authenticated:
			return None
		try:
			vote = self.likes.get(user=user)
			return 'like' if vote.is_like else 'dislike'
		except PhotoLike.DoesNotExist:
			return None

	class Meta:
		ordering = ['-uploaded_at']
class PhotoComment(models.Model):
	photo = models.ForeignKey('Photo', on_delete=models.CASCADE, related_name='comments')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
	username = models.CharField(max_length=100, blank=True, default='Anonymous')
	text = models.TextField(max_length=500)
	created_at = models.DateTimeField(auto_now_add=True)
	parent_comment = models.ForeignKey(
		'self', 
		on_delete=models.CASCADE, 
		null=True, 
		blank=True, 
		related_name='replies'
	)
	
	# Anonymous commenter support
	anonymous_email = models.EmailField(blank=True, help_text='Optional email for anonymous users')

	def __str__(self):
		return f"{self.username}: {self.text[:30]}"
	
	@property
	def is_anonymous(self):
		"""Check if this is an anonymous comment"""
		return self.user is None
	
	@property
	def display_name(self):
		"""Get display name for commenter"""
		if self.user:
			return self.user.get_full_name() or self.user.username
		return self.username or 'Anonymous'
	
	@property
	def replies_count(self):
		"""Get count of replies to this comment"""
		return self.replies.count()

	class Meta:
		ordering = ['created_at']  # Show oldest first for threaded conversation


# Story model for photographers
from datetime import timedelta
class Story(models.Model):
	photographer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
	image = models.ImageField(upload_to='stories/', blank=True, null=True)
	video = models.FileField(upload_to='stories/videos/', blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		if self.image:
			from PIL import Image
			img = Image.open(self.image.path)
			# Keep stories at a higher resolution than before for clearer previews
			max_size = (1280, 1280)
			img.thumbnail(max_size, Image.LANCZOS)
			img.save(self.image.path, optimize=True, quality=90)
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
	image = models.ImageField(upload_to='event_photos/', blank=True, null=True)
	video = models.FileField(upload_to='event_videos/', blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.title} by {self.photographer.get_full_name()} on {self.date}"
	
	


# Contact Us message model
class ContactMessage(models.Model):
	name = models.CharField(max_length=100)
	email = models.EmailField()
	message = models.TextField()
	submitted_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.name} ({self.email}) - {self.submitted_at:%Y-%m-%d %H:%M}"

# Editable legal content models
class PrivacyPolicy(models.Model):
	from ckeditor.fields import RichTextField
	content = RichTextField()
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Privacy Policy (updated {self.updated_at:%Y-%m-%d})"

class TermsOfService(models.Model):
	from ckeditor.fields import RichTextField
	content = RichTextField()
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Terms of Service (updated {self.updated_at:%Y-%m-%d})"


def reprocess_images(dry_run=False, limit=0):
	"""Reprocess Photo and Story images using current model save rules.

	This helper is placed in `portfolio.models` so you can call it from the
	Django shell instead of using a separate management command file.

	Usage (Django shell):
		from portfolio.models import reprocess_images
		reprocess_images(dry_run=True, limit=10)

	Arguments:
		dry_run (bool): If True, only report which files would be processed.
		limit (int): Optional limit to number of objects to process.
	"""
	photos = Photo.objects.all()
	stories = Story.objects.all()

	total = photos.count() + stories.count()
	print(f'Found {total} images to potentially reprocess ({photos.count()} photos, {stories.count()} stories)')

	processed = 0
	for qs, name in ((photos, 'Photo'), (stories, 'Story')):
		for obj in qs:
			if limit and processed >= limit:
				break
			path = getattr(getattr(obj, 'image', None), 'path', None)
			if not path:
				print(f'Skipping {name} id={obj.pk}: no image')
				continue
			print(f'Processing {name} id={obj.pk}: {getattr(obj.image, "url", "<no url>")}')
			if not dry_run:
				try:
					obj.save()
					print(f'Reprocessed {name} id={obj.pk}')
				except Exception as e:
					print(f'Error processing {name} id={obj.pk}: {e}')
			processed += 1

	print(f'Done. Processed {processed} items.')
	return processed
