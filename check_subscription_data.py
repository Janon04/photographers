#!/usr/bin/env python
"""
Script to check and create test subscription data if needed
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from payments.models import SubscriptionPlan, UserSubscription, SubscriptionPayment
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def check_subscription_data():
    """Check current subscription data"""
    print("=== Current Subscription Data ===")
    
    # Check plans
    plans = SubscriptionPlan.objects.all()
    print(f"Subscription Plans: {plans.count()}")
    for plan in plans:
        print(f"  - {plan.display_name}: {plan.price_monthly} {plan.currency}")
    
    # Check subscriptions
    subscriptions = UserSubscription.objects.all()
    print(f"\nUser Subscriptions: {subscriptions.count()}")
    for sub in subscriptions:
        print(f"  - {sub.user.username}: {sub.plan.display_name} ({sub.status})")
    
    # Check payments
    payments = SubscriptionPayment.objects.all()
    print(f"\nSubscription Payments: {payments.count()}")
    for payment in payments:
        print(f"  - {payment.subscription.user.username}: {payment.amount} {payment.currency} ({payment.status})")
    
    return plans.count(), subscriptions.count(), payments.count()

def create_test_data():
    """Create test subscription data"""
    print("\n=== Creating Test Data ===")
    
    # Get or create test users
    test_users = []
    for i in range(3):
        username = f"testuser{i+1}"
        email = f"testuser{i+1}@example.com"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': f'Test',
                'last_name': f'User {i+1}',
                'role': User.Roles.PHOTOGRAPHER
            }
        )
        test_users.append(user)
        if created:
            print(f"Created user: {username}")
    
    # Create subscription plans if they don't exist
    plans_data = [
        {'name': 'basic', 'display_name': 'Basic Plan', 'price_monthly': Decimal('2000')},
        {'name': 'standard', 'display_name': 'Standard Plan', 'price_monthly': Decimal('15000')},
        {'name': 'premium', 'display_name': 'Premium Plan', 'price_monthly': Decimal('35000')},
    ]
    
    plans = []
    for plan_data in plans_data:
        plan, created = SubscriptionPlan.objects.get_or_create(
            name=plan_data['name'],
            defaults={
                'display_name': plan_data['display_name'],
                'price_monthly': plan_data['price_monthly'],
                'currency': 'RWF',
                'features_description': f'{plan_data["display_name"]} features',
                'support_level': 'Standard',
                'customization_level': 'Basic',
                'max_photos_upload': 100,
                'max_storage_gb': 10,
                'max_bookings_per_month': 50,
                'max_portfolio_items': 20,
                'additional_services': 'Basic support',
                'commission_rate': Decimal('10.00')
            }
        )
        plans.append(plan)
        if created:
            print(f"Created plan: {plan.display_name}")
    
    # Create test subscriptions
    for i, user in enumerate(test_users):
        # Check if user already has a subscription
        if not hasattr(user, 'subscription'):
            plan = plans[i % len(plans)]  # Distribute users across plans
            subscription = UserSubscription.objects.create(
                user=user,
                plan=plan,
                status='active',
                billing_cycle='monthly',
                expires_at=timezone.now() + timedelta(days=30)
            )
            print(f"Created subscription: {user.username} -> {plan.display_name}")
            
            # Create a payment for this subscription
            payment = SubscriptionPayment.objects.create(
                subscription=subscription,
                amount=plan.price_monthly,
                currency='RWF',
                billing_period_start=timezone.now(),
                billing_period_end=timezone.now() + timedelta(days=30),
                payment_method='Card',
                payment_gateway='Test Gateway',
                status='completed',
                paid_at=timezone.now()
            )
            print(f"Created payment: {payment.amount} RWF for {user.username}")

if __name__ == "__main__":
    # Check current data
    plans_count, subs_count, payments_count = check_subscription_data()
    
    # Create test data if needed
    if plans_count == 0 or subs_count == 0 or payments_count == 0:
        print("\nNo sufficient subscription data found. Creating test data...")
        create_test_data()
        print("\n=== Updated Data ===")
        check_subscription_data()
    else:
        print("\nSubscription data already exists!")
    
    print("\nDone!")