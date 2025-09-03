from django.urls import path
from . import views

urlpatterns = [
    path('transactions/', views.transaction_history, name='transaction_history'),
    path('earnings/', views.earnings_dashboard, name='earnings_dashboard'),
]
