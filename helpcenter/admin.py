from ckeditor.widgets import CKEditorWidget
from django.contrib import admin
from .models import HelpCategory, HelpArticle, UserQuestion

# Admin for user-submitted questions
@admin.register(UserQuestion)
class UserQuestionAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'question', 'submitted_at')
    search_fields = ('name', 'email', 'question')

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
