from django.urls import path

from . import views

app_name = 'portfolio'

urlpatterns = [
    path('', views.photographer_list, name='portfolio_home'),
    path('dashboard/', views.photographer_dashboard, name='photographer_dashboard'),
    path('feed/', views.feed, name='feed'),
    path('stories/upload/', views.upload_story, name='upload_story'),
    path('photographers/', views.photographer_list, name='photographer_list'),
    path('photographer/<int:pk>/', views.photographer_detail, name='photographer_detail'),
    path('photos/', views.photo_list, name='photo_list'),
    path('category/<int:category_id>/', views.category_photos, name='category_photos'),
    path('upload/', views.upload_photo, name='upload_photo'),
    path('add-category/', views.add_category, name='add_category'),
    # Event URLs
    path('events/', views.my_events, name='my_events'),
    path('events/create/', views.create_event, name='create_event'),
    path('story/<int:story_id>/delete/', views.delete_story, name='delete_story'),
    path('photo/<int:photo_id>/delete/', views.delete_photo, name='delete_photo'),
    path('like_photo/', views.like_photo, name='like_photo'),
    path('dislike_photo/', views.dislike_photo, name='dislike_photo'),
    path('add_comment/', views.add_comment, name='add_comment'),
    path('share_photo/', views.share_photo, name='share_photo'),
    
    # New photo interaction endpoints
    path('photo/<int:photo_id>/like/', views.toggle_photo_like, name='toggle_photo_like'),
    path('photo/<int:photo_id>/dislike/', views.toggle_photo_dislike, name='toggle_photo_dislike'),
    path('photo/<int:photo_id>/comment/', views.add_photo_comment, name='add_photo_comment'),
    path('photo/<int:photo_id>/comments/', views.get_photo_comments, name='get_photo_comments'),
    
    # AI-Powered Features
    path('ai-insights/', views.ai_insights, name='ai_insights'),
    path('auto-categorize/', views.auto_categorize_photos, name='auto_categorize'),
    path('seo-optimizer/', views.seo_optimizer, name='seo_optimizer'),
]
