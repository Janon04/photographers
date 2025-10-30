from ckeditor.widgets import CKEditorWidget
from django.contrib import admin
from .models import HelpCategory, HelpArticle, UserQuestion

from ckeditor.widgets import CKEditorWidget
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from .models import HelpCategory, HelpArticle, UserQuestion
from config.email_service import EmailService
import logging

logger = logging.getLogger(__name__)

# Admin for user-submitted questions with enhanced functionality
@admin.register(UserQuestion)
class UserQuestionAdmin(admin.ModelAdmin):
    list_display = (
        'colored_status', 'priority_display', 'name', 'email', 
        'question_preview', 'submitted_at', 'responded_at', 'action_buttons'
    )
    list_filter = (
        'status', 'priority', 'is_pinned', 'is_faq', 'faq_category', 
        'submitted_at', 'responded_at'
    )
    search_fields = ('name', 'email', 'question', 'admin_response', 'faq_title')
    ordering = ['-is_pinned', '-priority', '-submitted_at']
    
    fieldsets = (
        ('Question Details', {
            'fields': ('name', 'email', 'question', 'submitted_at'),
            'classes': ('wide',)
        }),
        ('Admin Response', {
            'fields': ('admin_response', 'responded_by', 'responded_at', 'status'),
            'classes': ('wide',)
        }),
        ('Organization & FAQ', {
            'fields': ('priority', 'is_pinned', 'is_faq', 'faq_title', 'faq_category'),
            'classes': ('wide',)
        }),
        ('Internal Notes', {
            'fields': ('admin_notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('submitted_at', 'responded_at')
    
    actions = [
        'mark_as_responded', 'mark_as_pending', 'mark_as_closed',
        'pin_questions', 'unpin_questions', 'mark_as_faq', 'unmark_as_faq',
        'send_response_email'
    ]
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Auto-fill responded_by when adding a response
        if obj and obj.admin_response and not obj.responded_by:
            form.base_fields['responded_by'].initial = request.user
        return form
    
    def save_model(self, request, obj, form, change):
        # Auto-set responded_by when admin adds a response
        if obj.admin_response and not obj.responded_by:
            obj.responded_by = request.user
            if not obj.responded_at:
                obj.responded_at = timezone.now()
        
        # Auto-send email when response is added for the first time
        old_obj = None
        if change:
            old_obj = UserQuestion.objects.get(pk=obj.pk)
        
        super().save_model(request, obj, form, change)
        
        # Send email if response was just added
        if (obj.admin_response and 
            (not old_obj or not old_obj.admin_response) and 
            obj.email):
            try:
                EmailService.send_help_response_notification(obj)
                messages.success(request, f"Response email sent to {obj.email}")
            except Exception as e:
                messages.warning(request, f"Response saved but email failed: {e}")
    
    def colored_status(self, obj):
        colors = {
            'pending': '#ff9800',
            'responded': '#4caf50', 
            'closed': '#9e9e9e'
        }
        icons = {
            'pending': '⏳',
            'responded': '✅',
            'closed': '🔒'
        }
        color = colors.get(obj.status, '#333')
        icon = icons.get(obj.status, '❓')
        pin = '📌' if obj.is_pinned else ''
        faq = '🔖' if obj.is_faq else ''
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{}{} {}</span>',
            color, pin, faq, icon, obj.get_status_display()
        )
    colored_status.short_description = 'Status'
    
    def priority_display(self, obj):
        colors = {
            'urgent': '#f44336',
            'high': '#ff9800',
            'normal': '#2196f3',
            'low': '#9e9e9e'
        }
        icons = {
            'urgent': '🔥',
            'high': '❗',
            'normal': '📝',
            'low': '💭'
        }
        color = colors.get(obj.priority, '#333')
        icon = icons.get(obj.priority, '📝')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_priority_display()
        )
    priority_display.short_description = 'Priority'
    
    def question_preview(self, obj):
        preview = obj.question[:100] + '...' if len(obj.question) > 100 else obj.question
        return format_html('<span title="{}">{}</span>', obj.question, preview)
    question_preview.short_description = 'Question'
    
    def action_buttons(self, obj):
        buttons = []
        
        if obj.status == 'pending':
            respond_url = reverse('admin:helpcenter_userquestion_change', args=[obj.pk])
            buttons.append(f'<a href="{respond_url}" style="background: #4caf50; color: white; padding: 2px 8px; border-radius: 3px; text-decoration: none; font-size: 11px;">📝 Respond</a>')
        
        if obj.admin_response and obj.email:
            buttons.append('<a onclick="return confirm(\'Send response email?\')" href="#" style="background: #2196f3; color: white; padding: 2px 8px; border-radius: 3px; text-decoration: none; font-size: 11px;">📧 Resend</a>')
        
        return format_html(' '.join(buttons))
    action_buttons.short_description = 'Actions'
    
    # Admin Actions
    def mark_as_responded(self, request, queryset):
        count = queryset.update(status='responded')
        messages.success(request, f'{count} questions marked as responded.')
    mark_as_responded.short_description = "Mark as responded"
    
    def mark_as_pending(self, request, queryset):
        count = queryset.update(status='pending')
        messages.success(request, f'{count} questions marked as pending.')
    mark_as_pending.short_description = "Mark as pending"
    
    def mark_as_closed(self, request, queryset):
        count = queryset.update(status='closed')
        messages.success(request, f'{count} questions marked as closed.')
    mark_as_closed.short_description = "Mark as closed"
    
    def pin_questions(self, request, queryset):
        count = queryset.update(is_pinned=True)
        messages.success(request, f'{count} questions pinned.')
    pin_questions.short_description = "📌 Pin questions"
    
    def unpin_questions(self, request, queryset):
        count = queryset.update(is_pinned=False)
        messages.success(request, f'{count} questions unpinned.')
    unpin_questions.short_description = "📌 Unpin questions"
    
    def mark_as_faq(self, request, queryset):
        count = queryset.update(is_faq=True)
        messages.success(request, f'{count} questions marked as FAQ.')
    mark_as_faq.short_description = "🔖 Mark as FAQ"
    
    def unmark_as_faq(self, request, queryset):
        count = queryset.update(is_faq=False)
        messages.success(request, f'{count} questions unmarked as FAQ.')
    unmark_as_faq.short_description = "🔖 Unmark as FAQ"
    
    def send_response_email(self, request, queryset):
        sent_count = 0
        for question in queryset:
            if question.admin_response and question.email:
                try:
                    EmailService.send_help_response_notification(question)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send response email for question {question.id}: {e}")
        
        if sent_count > 0:
            messages.success(request, f'Response emails sent for {sent_count} questions.')
        else:
            messages.warning(request, 'No emails sent. Questions need both response and email address.')
    send_response_email.short_description = "📧 Send response emails"

class HelpArticleInline(admin.TabularInline):
    model = HelpArticle
    extra = 1

@admin.register(HelpCategory)
class HelpCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    inlines = [HelpArticleInline]
    formfield_overrides = {
        HelpCategory.description.field: {'widget': CKEditorWidget},
    }

@admin.register(HelpArticle)
class HelpArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_faq', 'created_at', 'updated_at')
    list_filter = ('category', 'is_faq')
    search_fields = ('title', 'content')
    formfield_overrides = {
        HelpArticle.content.field: {'widget': CKEditorWidget},
    }
