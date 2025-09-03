from django.urls import path
from . import views
from django.shortcuts import redirect

def reviews_home(request):
    return redirect('reviews_list')

urlpatterns = [
    path('', reviews_home, name='reviews_home'),
    path('add/', views.add_review, name='add_review'),
    path('all/', views.reviews_list, name='reviews_list'),
]
