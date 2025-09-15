

from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Photo, Event

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
