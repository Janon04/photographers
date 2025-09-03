
from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
	list_display = ('reviewer', 'photographer', 'rating', 'created_at')
	list_filter = ('rating', 'created_at')
	search_fields = ('reviewer__email', 'photographer__email', 'comment')
