from django.urls import path
from . import views
from django.shortcuts import redirect

app_name = 'reviews'

def reviews_home(request):
    return redirect('reviews:reviews_list')

urlpatterns = [
    # Main review pages
    path('', reviews_home, name='reviews_home'),
    path('all/', views.reviews_list, name='reviews_list'),
    path('add/', views.add_review, name='add_review'),
    path('<int:review_id>/', views.review_detail, name='review_detail'),
    
    # Review interactions
    path('<int:review_id>/vote/', views.vote_helpfulness, name='vote_helpfulness'),
    path('<int:review_id>/respond/', views.add_response, name='add_response'),
    
    # Photographer-specific views
    path('photographer/<int:photographer_id>/', views.photographer_reviews, name='photographer_reviews'),
    path('photographer/<int:photographer_id>/public-analytics/', views.public_analytics, name='public_analytics'),
    
    # Analytics and reports (photographer only)
    path('sentiment-report/', views.sentiment_report, name='sentiment_report'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
]
