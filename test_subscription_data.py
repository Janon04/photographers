#!/usr/bin/env python
"""Test script to check and create subscription data for testing"""

import os
import sys
import django
from decimal import Decimal
from datetime import timedelta

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from payments.models import SubscriptionPlan, UserSubscription, SubscriptionPayment
from users.models import User

def check_existing_data():
    """Check existing subscription data"""
    print("=== Existing Data Check ===")
    
    # Check users
    users_count = User.objects.count()
    print(f"Total Users: {users_count}")
    
    # Check subscription plans
    plans_count = SubscriptionPlan.objects.count()
    print(f"Total Subscription Plans: {plans_count}")
    
    # List plans
    for plan in SubscriptionPlan.objects.all():
        print(f"  - {plan.display_name}: {plan.price_monthly} {plan.currency}/month")
    
    # Check user subscriptions
    subscriptions_count = UserSubscription.objects.count()
    print(f"Total User Subscriptions: {subscriptions_count}")
    
    # Check subscription payments
    payments_count = SubscriptionPayment.objects.count()
    print(f"Total Subscription Payments: {payments_count}")
    
    return users_count, plans_count, subscriptions_count, payments_count

def create_test_data():
    """Create test subscription data if needed"""
    print("\n=== Creating Test Data ===")
    
    # Create subscription plans if they don't exist
    if not SubscriptionPlan.objects.exists():
        print("Creating subscription plans...")
        
        basic_plan = SubscriptionPlan.objects.create(
            name='basic',
            display_name='Basic Plan',
            price_monthly=Decimal('15000'),  # 15,000 RWF
            price_yearly=Decimal('150000'),  # 150,000 RWF
            currency='RWF',
            features_description='• Up to 100 photos per month\n• 5GB storage\n• Basic portfolio\n• Community access',
            support_level='Email Support',
            customization_level='Basic',
            max_photos_upload=100,
            max_storage_gb=5,
            max_bookings_per_month=10,
            max_portfolio_items=50,
            additional_services='Basic customer support',
            commission_rate=Decimal('10.00'),
        )
        
        standard_plan = SubscriptionPlan.objects.create(
            name='standard',
            display_name='Standard Plan',
            price_monthly=Decimal('25000'),  # 25,000 RWF
            price_yearly=Decimal('250000'),  # 250,000 RWF
            currency='RWF',
            features_description='• Up to 500 photos per month\n• 25GB storage\n• Advanced portfolio\n• Priority booking\n• Analytics access',
            support_level='Priority Email Support',
            customization_level='Advanced',
            max_photos_upload=500,
            max_storage_gb=25,
            max_bookings_per_month=50,
            max_portfolio_items=200,
            additional_services='Priority support, Analytics dashboard',
            commission_rate=Decimal('8.00'),
            analytics_access=True,
        )
        
        premium_plan = SubscriptionPlan.objects.create(
            name='premium',
            display_name='Premium Plan',
            price_monthly=Decimal('45000'),  # 45,000 RWF
            price_yearly=Decimal('450000'),  # 450,000 RWF
            currency='RWF',
            features_description='• Unlimited photos\n• Unlimited storage\n• Premium portfolio\n• Unlimited bookings\n• Premium support\n• API access',
            support_level='24/7 Phone & Email Support',
            customization_level='Premium',
            max_photos_upload=-1,  # Unlimited
            max_storage_gb=-1,     # Unlimited
            max_bookings_per_month=-1,  # Unlimited
            max_portfolio_items=-1,     # Unlimited
            additional_services='24/7 support, API access, Consulting sessions',
            commission_rate=Decimal('5.00'),
            priority_support=True,
            analytics_access=True,
            api_access=True,
            includes_premium_support=True,
            includes_consulting=True,
        )
        
        print(f"Created 3 subscription plans")
    
    # Create test users with subscriptions if needed
    if UserSubscription.objects.count() < 3:
        print("Creating test user subscriptions...")
        
        # Get or create test users
        users = []
        for i in range(1, 6):
            user, created = User.objects.get_or_create(
                username=f'photographer{i}',
                defaults={
                    'email': f'photographer{i}@example.com',
                    'first_name': f'Photographer',
                    'last_name': f'{i}',
                }
            )
            users.append(user)
            if created:
                print(f"  - Created user: {user.username}")
        
        # Create subscriptions
        plans = list(SubscriptionPlan.objects.all())
        
        for i, user in enumerate(users):
            if not hasattr(user, 'subscription'):
                plan = plans[i % len(plans)]  # Rotate through plans
                
                # Create subscription
                start_date = timezone.now() - timedelta(days=i*10)
                
                subscription = UserSubscription.objects.create(
                    user=user,
                    plan=plan,
                    billing_cycle='monthly' if i % 2 == 0 else 'yearly',
                    status='active' if i < 3 else 'trial',
                    start_date=start_date,
                    end_date=start_date + timedelta(days=30 if i % 2 == 0 else 365),
                    next_billing_date=start_date + timedelta(days=30 if i % 2 == 0 else 365),
                    photos_uploaded_this_month=i * 10,
                    storage_used_gb=Decimal(str(i * 2.5)),
                    bookings_this_month=i * 2,
                )
                
                print(f"  - Created subscription for {user.username}: {plan.display_name}")
                
                # Create payment history
                for j in range(1, 4):  # Create 3 payments per user
                    payment_date = start_date + timedelta(days=j*30)
                    
                    payment = SubscriptionPayment.objects.create(
                        subscription=subscription,
                        amount=plan.price_monthly,
                        currency='RWF',
                        billing_period_start=payment_date,
                        billing_period_end=payment_date + timedelta(days=30),
                        payment_method='Mobile Money' if j % 2 == 0 else 'Bank Transfer',
                        payment_gateway='MTN MoMo' if j % 2 == 0 else 'Bank of Rwanda',
                        status='completed' if j < 3 else 'pending',
                        payment_date=payment_date,
                    )
                    
                    print(f"    - Created payment: {payment.amount} RWF on {payment_date.strftime('%Y-%m-%d')}")

if __name__ == '__main__':
    # Check existing data
    users_count, plans_count, subscriptions_count, payments_count = check_existing_data()
    
    # Create test data if needed
    if plans_count == 0 or subscriptions_count < 3 or payments_count < 5:
        create_test_data()
        print("\n=== Updated Data Summary ===")
        check_existing_data()
    else:
        print("\nSufficient test data already exists!")
    
    print("\nTest script completed!")