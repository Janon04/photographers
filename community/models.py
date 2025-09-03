
from django.db import models
from users.models import User
from ckeditor.fields import RichTextField

class CommunityCategory(models.Model):
	name = models.CharField(max_length=100, unique=True)

	def __str__(self):
		return self.name

class Post(models.Model):
	title = models.CharField(max_length=255)
	description = models.TextField()
	content = RichTextField()
	date = models.DateTimeField(auto_now_add=True)
	image = models.ImageField(upload_to='community_posts/', blank=True, null=True)
	category = models.ForeignKey(CommunityCategory, on_delete=models.SET_NULL, null=True, related_name='posts')

	def __str__(self):
		return self.title
	from django.db import models
	from users.models import User

	class BlogPost(models.Model):
		author = models.ForeignKey(User, on_delete=models.CASCADE)
		title = models.CharField(max_length=255)
		content = models.TextField()
		created_at = models.DateTimeField(auto_now_add=True)

		def __str__(self):
			return self.title
