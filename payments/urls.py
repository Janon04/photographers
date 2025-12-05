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
    
    # Checkout URLs
    path('checkout/<int:booking_id>/', views.payment_checkout, name='payment_checkout'),
    path('checkout/<int:booking_id>/process/', views.process_booking_payment, name='process_booking_payment'),
    path('success/<uuid:transaction_id>/', views.payment_success, name='payment_success'),
    path('failed/<int:booking_id>/', views.payment_failed, name='payment_failed'),
    
    # Subscription URLs
    path('pricing/', views.pricing_page, name='pricing_page'),
    path('subscription/', views.subscription_dashboard, name='subscription_dashboard'),
    path('subscription/upgrade/', views.upgrade_subscription, name='upgrade_subscription'),
    path('subscription/checkout/<int:plan_id>/', views.subscription_checkout, name='subscription_checkout'),
    path('subscription/payment/process/', views.subscription_payment_process, name='subscription_payment_process'),
    path('billing/', views.billing_history, name='billing_history'),
]
