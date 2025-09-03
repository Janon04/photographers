from django.urls import path
from . import views

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
]
