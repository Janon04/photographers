
from django.contrib import admin
from .models import CommunityCategory, Post

@admin.register(CommunityCategory)
class CommunityCategoryAdmin(admin.ModelAdmin):
	list_display = ('name',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
	list_display = ('title', 'category', 'date')
	list_filter = ('category', 'date')
	search_fields = ('title', 'description', 'content')
