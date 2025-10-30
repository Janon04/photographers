from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    # Main dashboard
    path('', views.admin_dashboard, name='dashboard'),
    
    # User management
    path('users/', views.users_management, name='users_management'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/toggle-verification/', views.toggle_user_verification, name='toggle_user_verification'),
    path('users/<int:user_id>/suspend/', views.suspend_user, name='suspend_user'),
    
    # Booking management
    path('bookings/', views.bookings_management, name='bookings_management'),
    
    # Reviews management
    path('reviews/', views.reviews_management, name='reviews_management'),
    path('reviews/<int:review_id>/approve/', views.approve_review, name='approve_review'),
    
    # Analytics
    path('analytics/', views.analytics_dashboard, name='analytics'),
    
    # Notifications
    path('notifications/', views.notifications_management, name='notifications_management'),
    
    # Activity logs
    path('logs/', views.activity_logs, name='activity_logs'),
    
    # Data export
    path('export/', views.export_data, name='export_data'),
]