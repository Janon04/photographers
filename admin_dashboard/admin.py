from django.contrib import admin
from .models import AdminActivityLog, PlatformSettings, SystemNotification, PlatformAnalytics

@admin.register(AdminActivityLog)
class AdminActivityLogAdmin(admin.ModelAdmin):
    list_display = ('admin_user', 'action', 'target_model', 'target_description', 'timestamp')
    list_filter = ('action', 'target_model', 'timestamp')
    search_fields = ('admin_user__email', 'target_description', 'details')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)

@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'description', 'updated_by', 'updated_at')
    search_fields = ('key', 'description')
    readonly_fields = ('updated_at',)

@admin.register(SystemNotification)
class SystemNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'target_users', 'is_active', 'created_at', 'expires_at')
    list_filter = ('notification_type', 'target_users', 'is_active', 'created_at')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at',)

@admin.register(PlatformAnalytics)
class PlatformAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_users', 'total_bookings', 'total_revenue', 'created_at')
    list_filter = ('date', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('-date',)
