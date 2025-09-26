from django.urls import path
from . import views

urlpatterns = [
    path('', views.blog_list, name='blog_list'),
    path('post/<int:pk>/', views.blog_detail, name='blog_detail'),
    path('create/', views.blog_create, name='blog_create'),
    path('edit/<int:pk>/', views.blog_edit, name='blog_edit'),
]
