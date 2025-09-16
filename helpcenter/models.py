from django.db import models
from ckeditor.fields import RichTextField
# Model for user-submitted questions
class UserQuestion(models.Model):
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    question = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Question from {self.name or 'Anonymous'} at {self.submitted_at:%Y-%m-%d %H:%M}"

class HelpCategory(models.Model):
    name = models.CharField(max_length=100)
    description = RichTextField(blank=True)

    def __str__(self):
        return self.name

class HelpArticle(models.Model):
    category = models.ForeignKey(HelpCategory, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=200)
    content = RichTextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_faq = models.BooleanField(default=False)

    def __str__(self):
        return self.title
