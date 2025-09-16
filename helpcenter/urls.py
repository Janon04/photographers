from django.urls import path
from . import views

urlpatterns = [
    path('', views.helpcenter_home, name='helpcenter_home'),
    path('category/<int:category_id>/', views.helpcenter_category, name='helpcenter_category'),
    path('article/<int:article_id>/', views.helpcenter_article, name='helpcenter_article'),
]
