
from django.contrib import admin
from .models import Category, Photo

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name',)

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
	list_display = ('title', 'photographer', 'category', 'uploaded_at')
	search_fields = ('title', 'photographer__email')
	list_filter = ('category',)
