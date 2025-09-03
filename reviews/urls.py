from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_review, name='add_review'),
    path('all/', views.reviews_list, name='reviews_list'),
]
