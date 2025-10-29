from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('create/', views.create_booking, name='create_booking'),
    path('client/', views.client_dashboard, name='client_dashboard'),
    path('photographer/', views.photographer_dashboard, name='photographer_dashboard'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('confirm/<int:booking_id>/', views.confirm_booking, name='confirm_booking'),
    path('complete/<int:booking_id>/', views.complete_booking, name='complete_booking'),
    
    # AI Features
    path('pricing-calculator/', views.pricing_calculator, name='pricing_calculator'),
]
