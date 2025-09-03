
from django.contrib import admin
from .models import Category, Photo, Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
	list_display = ('title', 'photographer', 'date', 'location', 'created_at')
	search_fields = ('title', 'photographer__email', 'location')
	list_filter = ('date',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name',)

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
	list_display = ('title', 'photographer', 'category', 'uploaded_at')
	search_fields = ('title', 'photographer__email')
	list_filter = ('category',)
