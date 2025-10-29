from django.urls import path
from . import views
from django.shortcuts import redirect

def payments_home(request):
    if request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'photographer':
        return redirect('earnings_dashboard')
    return redirect('transaction_history')

urlpatterns = [
    path('', payments_home, name='payments_home'),
    path('transactions/', views.transaction_history, name='transaction_history'),
    path('earnings/', views.earnings_dashboard, name='earnings_dashboard'),
    path('process/', views.process_payment, name='process_payment'),
    path('retry/<int:transaction_id>/', views.retry_payment, name='retry_payment'),
]
