from django.urls import path
from . import views

urlpatterns = [
    path('like-photo/', views.like_photo, name='like_photo'),
    path('dislike-photo/', views.dislike_photo, name='dislike_photo'),
]
