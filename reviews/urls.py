from django.urls import path
from . import views
from django.shortcuts import redirect

app_name = 'reviews'

def reviews_home(request):
    return redirect('reviews:reviews_list')

urlpatterns = [
    path('', reviews_home, name='reviews_home'),
    path('add/', views.add_review, name='add_review'),
    path('all/', views.reviews_list, name='reviews_list'),
    path('sentiment-report/', views.sentiment_report, name='sentiment_report'),
]
