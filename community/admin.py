from ckeditor.widgets import CKEditorWidget

from django.contrib import admin
from .models import CommunityCategory, Post, ContentReport

@admin.register(ContentReport)
class ContentReportAdmin(admin.ModelAdmin):
	list_display = ('report_type', 'object_id', 'reporter', 'created_at', 'is_resolved')
	list_filter = ('report_type', 'is_resolved', 'created_at')
	search_fields = ('reporter__email', 'reason')

@admin.register(CommunityCategory)
class CommunityCategoryAdmin(admin.ModelAdmin):
	list_display = ('name',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
	list_display = ('title', 'category', 'date', 'is_approved')
	list_filter = ('category', 'date', 'is_approved')
	search_fields = ('title', 'description', 'content')
	formfield_overrides = {
		Post.content.field: {'widget': CKEditorWidget},
		Post.description.field: {'widget': CKEditorWidget},
	}
