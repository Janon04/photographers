#!/usr/bin/env python
"""Check subscription payment data in database"""

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

def check_payment_data():
    """Check existing payment data and show stats"""
    print("=== SUBSCRIPTION PAYMENT DATABASE CHECK ===")
    print()
    
    # Check subscription plans
    plans_count = SubscriptionPlan.objects.count()
    print(f"📋 Subscription Plans: {plans_count}")
    
    for plan in SubscriptionPlan.objects.all()[:3]:
        print(f"   - {plan.display_name}: {plan.price_monthly:,.0f} {plan.currency}/month")
    
    # Check user subscriptions
    subscriptions_count = UserSubscription.objects.count()
    print(f"\n👥 User Subscriptions: {subscriptions_count}")
    
    if subscriptions_count > 0:
        active_subs = UserSubscription.objects.filter(status='active').count()
        trial_subs = UserSubscription.objects.filter(status='trial').count()
        print(f"   - Active: {active_subs}")
        print(f"   - Trial: {trial_subs}")
    
    # Check subscription payments
    payments_count = SubscriptionPayment.objects.count()
    print(f"\n💰 Subscription Payments: {payments_count}")
    
    if payments_count > 0:
        completed = SubscriptionPayment.objects.filter(status='completed').count()
        pending = SubscriptionPayment.objects.filter(status='pending').count()
        failed = SubscriptionPayment.objects.filter(status='failed').count()
        
        print(f"   - Completed: {completed}")
        print(f"   - Pending: {pending}")
        print(f"   - Failed: {failed}")
        
        # Revenue calculation
        total_revenue = SubscriptionPayment.objects.filter(
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        monthly_revenue = SubscriptionPayment.objects.filter(
            status='completed',
            created_at__month=timezone.now().month,
            created_at__year=timezone.now().year
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        print(f"   - Total Revenue: {total_revenue:,.0f} RWF")
        print(f"   - Monthly Revenue: {monthly_revenue:,.0f} RWF")
        
        # Show recent payments
        print(f"\n📝 Recent Payments:")
        recent_payments = SubscriptionPayment.objects.select_related(
            'subscription__user', 'subscription__plan'
        ).order_by('-created_at')[:5]
        
        for payment in recent_payments:
            user = payment.subscription.user
            plan = payment.subscription.plan
            print(f"   - {user.username} | {plan.display_name} | {payment.amount:,.0f} RWF | {payment.status}")
    else:
        print("   No payments found in database")
        print("\n💡 Would you like to create some test payment data? (y/n)")
        response = input().lower().strip()
        
        if response == 'y':
            create_test_payment_data()

def create_test_payment_data():
    """Create test payment data for demonstration"""
    print("\n=== CREATING TEST PAYMENT DATA ===")
    
    # First ensure we have plans and users
    if not SubscriptionPlan.objects.exists():
        print("Creating subscription plans...")
        create_subscription_plans()
    
    # Create test users if needed
    users = []
    for i in range(1, 6):
        user, created = User.objects.get_or_create(
            username=f'photographer{i}',
            defaults={
                'email': f'photographer{i}@example.com',
                'first_name': f'Photographer',
                'last_name': f'{i}',
                'role': User.Roles.PHOTOGRAPHER,
            }
        )
        users.append(user)
        if created:
            print(f"   Created user: {user.username}")
    
    # Create subscriptions and payments
    plans = list(SubscriptionPlan.objects.all())
    
    for i, user in enumerate(users):
        # Create subscription if it doesn't exist
        subscription, created = UserSubscription.objects.get_or_create(
            user=user,
            defaults={
                'plan': plans[i % len(plans)],
                'billing_cycle': 'monthly' if i % 2 == 0 else 'yearly',
                'status': 'active' if i < 3 else 'trial',
                'start_date': timezone.now() - timedelta(days=i*15),
                'end_date': timezone.now() + timedelta(days=30),
                'next_billing_date': timezone.now() + timedelta(days=30),
            }
        )
        
        if created:
            print(f"   Created subscription for {user.username}")
        
        # Create payment history for this subscription
        plan = subscription.plan
        
        # Create 3-5 payments per user
        payment_count = 3 + (i % 3)  # 3-5 payments
        
        for j in range(payment_count):
            payment_date = timezone.now() - timedelta(days=j*30 + i*5)
            
            # Different payment statuses for variety
            if j == 0:  # Most recent payment
                status = 'completed'
            elif j == 1 and i % 4 == 0:  # Some pending payments
                status = 'pending'
            elif j == payment_count - 1 and i % 5 == 0:  # Some failed payments
                status = 'failed'
            else:
                status = 'completed'
            
            payment, created = SubscriptionPayment.objects.get_or_create(
                subscription=subscription,
                billing_period_start=payment_date,
                billing_period_end=payment_date + timedelta(days=30),
                defaults={
                    'amount': plan.price_monthly,
                    'currency': 'RWF',
                    'payment_method': 'Mobile Money' if j % 2 == 0 else 'Bank Transfer',
                    'payment_gateway': 'MTN MoMo' if j % 2 == 0 else 'Bank of Rwanda',
                    'status': status,
                    'payment_date': payment_date,
                    'created_at': payment_date,
                }
            )
            
            if created:
                print(f"     Payment: {payment.amount:,.0f} RWF ({status}) - {payment_date.strftime('%Y-%m-%d')}")
    
    print(f"\n✅ Test payment data created successfully!")
    print(f"   Run the check again to see the updated stats")

def create_subscription_plans():
    """Create basic subscription plans"""
    plans_data = [
        {
            'name': 'basic',
            'display_name': 'Basic Plan',
            'price_monthly': Decimal('15000'),
            'features_description': 'Basic photography platform access with essential features',
        },
        {
            'name': 'standard', 
            'display_name': 'Standard Plan',
            'price_monthly': Decimal('25000'),
            'features_description': 'Enhanced features with priority support and analytics',
        },
        {
            'name': 'premium',
            'display_name': 'Premium Plan', 
            'price_monthly': Decimal('45000'),
            'features_description': 'Full-featured plan with unlimited access and premium support',
        }
    ]
    
    for plan_data in plans_data:
        plan, created = SubscriptionPlan.objects.get_or_create(
            name=plan_data['name'],
            defaults={
                'display_name': plan_data['display_name'],
                'price_monthly': plan_data['price_monthly'],
                'currency': 'RWF',
                'features_description': plan_data['features_description'],
                'support_level': 'Email Support',
                'customization_level': 'Basic',
                'max_photos_upload': 100,
                'max_storage_gb': 5,
                'max_bookings_per_month': 10,
                'max_portfolio_items': 50,
                'additional_services': 'Basic services',
                'commission_rate': Decimal('10.00'),
            }
        )
        if created:
            print(f"   Created plan: {plan.display_name}")

if __name__ == '__main__':
    # Import models here to avoid import before Django setup
    from django.db import models
    
    check_payment_data()