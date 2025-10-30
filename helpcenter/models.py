from django.db import models
from ckeditor.fields import RichTextField
from django.db import models
from ckeditor.fields import RichTextField
from django.contrib.auth import get_user_model

User = get_user_model()

# Model for user-submitted questions
class UserQuestion(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Response'),
        ('responded', 'Responded'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    question = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    # Response functionality
    admin_response = RichTextField(blank=True, help_text="Admin response to this question")
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   help_text="Admin who responded to this question")
    responded_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # FAQ and pinning functionality
    is_pinned = models.BooleanField(default=False, help_text="Pin this question for admin visibility")
    is_faq = models.BooleanField(default=False, help_text="Mark as Frequently Asked Question")
    faq_title = models.CharField(max_length=200, blank=True, help_text="Title for FAQ display")
    faq_category = models.ForeignKey('HelpCategory', on_delete=models.SET_NULL, null=True, blank=True,
                                   help_text="Category for FAQ organization")
    
    # Internal notes
    admin_notes = models.TextField(blank=True, help_text="Internal notes for admins (not sent to user)")
    
    class Meta:
        ordering = ['-is_pinned', '-priority', '-submitted_at']
        verbose_name = "User Question"
        verbose_name_plural = "User Questions"

    def __str__(self):
        status_emoji = {
            'pending': '⏳',
            'responded': '✅',
            'closed': '🔒'
        }
        priority_emoji = {
            'urgent': '🔥',
            'high': '❗',
            'normal': '📝',
            'low': '💭'
        }
        
        emoji = status_emoji.get(self.status, '❓')
        priority = priority_emoji.get(self.priority, '📝')
        pin = '📌' if self.is_pinned else ''
        faq = '🔖' if self.is_faq else ''
        
        return f"{pin}{faq}{emoji}{priority} {self.name or 'Anonymous'} - {self.submitted_at:%Y-%m-%d %H:%M}"
    
    def save(self, *args, **kwargs):
        # Auto-update status when response is added
        if self.admin_response and not self.responded_at:
            from django.utils import timezone
            self.responded_at = timezone.now()
            if self.status == 'pending':
                self.status = 'responded'
        super().save(*args, **kwargs)

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
