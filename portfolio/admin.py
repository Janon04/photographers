from ckeditor.widgets import CKEditorWidget

from django.contrib import admin
from .models import PrivacyPolicy, TermsOfService

@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(admin.ModelAdmin):
	list_display = ('updated_at',)
	search_fields = ('content',)
	readonly_fields = ('updated_at',)
	formfield_overrides = {
		PrivacyPolicy.content.field: {'widget': CKEditorWidget},
	}

@admin.register(TermsOfService)
class TermsOfServiceAdmin(admin.ModelAdmin):
	list_display = ('updated_at',)
	search_fields = ('content',)
	readonly_fields = ('updated_at',)
	formfield_overrides = {
		TermsOfService.content.field: {'widget': CKEditorWidget},
	}


from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Photo, Event
from .models import ContactMessage
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
	list_display = ('name', 'email', 'submitted_at')
	search_fields = ('name', 'email', 'message')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
	list_display = ('cover_image_tag', 'title', 'photographer', 'date', 'location', 'created_at')
	search_fields = ('title', 'photographer__email', 'location')
	list_filter = ('date',)
	readonly_fields = ('cover_image_tag',)

	def cover_image_tag(self, obj):
		if obj.image:
			return format_html('<img src="{}" style="max-height: 80px; max-width: 120px; object-fit: cover; border-radius: 6px;" />', obj.image.url)
		return "No Image"
	cover_image_tag.short_description = 'Cover'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name',)

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
	list_display = ('title', 'photographer', 'category', 'uploaded_at', 'is_approved')
	search_fields = ('title', 'photographer__email')
	list_filter = ('category', 'is_approved')
	formfield_overrides = {
		Photo.description.field: {'widget': CKEditorWidget},
	}
