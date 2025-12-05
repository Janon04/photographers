from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    # Main dashboard
    path('', views.admin_dashboard, name='dashboard'),
    
    # User management
    path('users/', views.users_management, name='users_management'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/details/', views.user_details_json, name='user_details_json'),
    path('users/<int:user_id>/toggle-verification/', views.toggle_user_verification, name='toggle_user_verification'),
    path('users/<int:user_id>/suspend/', views.suspend_user, name='suspend_user'),
    
    # Booking management
    path('bookings/', views.bookings_management, name='bookings_management'),
    path('bookings/<int:booking_id>/details/', views.booking_details_json, name='booking_details_json'),
    
    # Reviews management
    path('reviews/', views.reviews_management, name='reviews_management'),
    path('reviews/<int:review_id>/approve/', views.approve_review, name='approve_review'),
    path('reviews/<int:review_id>/details/', views.review_details_json, name='review_details_json'),
    
    # Analytics
    path('analytics/', views.analytics_dashboard, name='analytics'),
    
    # Notifications
    path('notifications/', views.notifications_management, name='notifications_management'),
    
    # Notification email endpoints (for new notifications)
    path('notifications/preview-email/', views.preview_notification_email, name='preview_notification_email'),
    path('notifications/send-email/', views.send_notification_email, name='send_notification_email'),
    path('notifications/recipient-count/', views.get_recipient_count, name='get_recipient_count'),
    
    # Existing notification endpoints
    path('notifications/<int:notification_id>/preview-existing/', views.preview_existing_notification_email, name='preview_existing_notification_email'),
    path('notifications/<int:notification_id>/send-existing/', views.send_existing_notification_email, name='send_existing_notification_email'),
    path('notifications/<int:notification_id>/toggle/', views.toggle_notification, name='toggle_notification'),
    path('notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    
    # Activity logs
    path('logs/', views.activity_logs, name='activity_logs'),
    
    # Data export
    path('export/', views.export_data, name='export_data'),
    
    # Subscription Management
    path('subscriptions/plans/', views.subscription_plans_management, name='subscription_plans'),
    path('subscriptions/plans/add/', views.subscription_plan_add, name='subscription_plan_add'),
    path('subscriptions/plans/<int:plan_id>/edit/', views.subscription_plan_edit, name='subscription_plan_edit'),
    path('subscriptions/plans/<int:plan_id>/delete/', views.subscription_plan_delete, name='subscription_plan_delete'),
    path('subscriptions/users/', views.subscription_users_management, name='subscription_users'),
    path('subscriptions/payments/', views.subscription_payments_management, name='subscription_payments'),
    
    # Platform Revenue Management
    path('revenue/', views.platform_revenue_management, name='platform_revenue'),
    
    # API endpoints
    path('api/subscription-stats/', views.subscription_stats_api, name='subscription_stats_api'),
    path('api/payment-details/<int:payment_id>/', views.payment_details_api, name='payment_details_api'),
]