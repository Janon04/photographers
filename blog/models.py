from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name

class BlogPost(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def total_likes(self):
        return self.likes.count()

    @property
    def total_dislikes(self):
        return self.dislikes.count()

    @property
    def total_comments(self):
        return self.comments.filter(is_approved=True).count()

class BlogComment(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    author_name = models.CharField(max_length=100, blank=True, null=True)  # For anonymous users
    author_email = models.EmailField(blank=True, null=True)  # For anonymous users
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)
    
    def __str__(self):
        author_display = self.author.username if self.author else self.author_name or "Anonymous"
        return f"Comment by {author_display} on {self.post}"

    @property
    def author_display(self):
        if self.author:
            return self.author.get_full_name() or self.author.username
        return self.author_name or "Anonymous"

class BlogLike(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)  # For anonymous users
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # For anonymous users
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [
            ['post', 'user'],  # Authenticated users can only like once
            ['post', 'session_key', 'ip_address'],  # Anonymous users by session+IP
        ]

    def __str__(self):
        if self.user:
            return f"{self.user.username} likes {self.post.title}"
        return f"Anonymous like on {self.post.title}"

class BlogDislike(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='dislikes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)  # For anonymous users
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # For anonymous users
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [
            ['post', 'user'],  # Authenticated users can only dislike once
            ['post', 'session_key', 'ip_address'],  # Anonymous users by session+IP
        ]

    def __str__(self):
        if self.user:
            return f"{self.user.username} dislikes {self.post.title}"
        return f"Anonymous dislike on {self.post.title}"
