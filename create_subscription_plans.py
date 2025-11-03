#!/usr/bin/env python
"""Create initial subscription plans"""

import os
import sys
import django
from decimal import Decimal

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from payments.models import SubscriptionPlan

def create_subscription_plans():
    """Create initial subscription plans"""
    
    # Check if plans already exist
    if SubscriptionPlan.objects.exists():
        print("Subscription plans already exist:")
        for plan in SubscriptionPlan.objects.all():
            print(f"  - {plan.display_name}: {plan.price_monthly} {plan.currency}/month")
        return
    
    print("Creating subscription plans...")
    
    # Basic Plan
    basic_plan = SubscriptionPlan.objects.create(
        name='basic',
        display_name='Basic Plan',
        price_monthly=Decimal('15000'),  # 15,000 RWF
        price_yearly=Decimal('150000'),  # 150,000 RWF (2 months free)
        currency='RWF',
        features_description='''• Upload up to 100 photos per month
• 5GB cloud storage
• Basic portfolio showcase
• Community forum access
• Email support''',
        support_level='Email Support',
        customization_level='Basic Templates',
        max_photos_upload=100,
        max_storage_gb=5,
        max_bookings_per_month=10,
        max_portfolio_items=50,
        additional_services='Community forum access, Basic templates',
        commission_rate=Decimal('10.00'),
        priority_support=False,
        analytics_access=False,
        api_access=False,
        includes_premium_support=False,
        includes_consulting=False,
        includes_add_ons=False,
    )
    
    # Standard Plan
    standard_plan = SubscriptionPlan.objects.create(
        name='standard',
        display_name='Standard Plan',
        price_monthly=Decimal('25000'),  # 25,000 RWF
        price_yearly=Decimal('250000'),  # 250,000 RWF (2 months free)
        currency='RWF',
        features_description='''• Upload up to 500 photos per month
• 25GB cloud storage
• Advanced portfolio customization
• Priority booking system
• Analytics dashboard
• Priority email support''',
        support_level='Priority Email Support',
        customization_level='Advanced Templates',
        max_photos_upload=500,
        max_storage_gb=25,
        max_bookings_per_month=50,
        max_portfolio_items=200,
        additional_services='Analytics dashboard, Advanced templates, Priority support',
        commission_rate=Decimal('8.00'),
        priority_support=True,
        analytics_access=True,
        api_access=False,
        includes_premium_support=False,
        includes_consulting=False,
        includes_add_ons=True,
    )
    
    # Premium Plan
    premium_plan = SubscriptionPlan.objects.create(
        name='premium',
        display_name='Premium Plan',
        price_monthly=Decimal('45000'),  # 45,000 RWF
        price_yearly=Decimal('450000'),  # 450,000 RWF (2 months free)
        currency='RWF',
        features_description='''• Unlimited photo uploads
• Unlimited cloud storage
• Premium portfolio themes
• Unlimited bookings
• Advanced analytics & insights
• 24/7 phone & email support
• API access for integrations
• Monthly consulting sessions''',
        support_level='24/7 Phone & Email Support',
        customization_level='Premium & Custom Themes',
        max_photos_upload=-1,  # Unlimited
        max_storage_gb=-1,     # Unlimited
        max_bookings_per_month=-1,  # Unlimited
        max_portfolio_items=-1,     # Unlimited
        additional_services='24/7 support, API access, Monthly consulting, Premium themes',
        commission_rate=Decimal('5.00'),
        priority_support=True,
        analytics_access=True,
        api_access=True,
        includes_premium_support=True,
        includes_consulting=True,
        includes_add_ons=True,
    )
    
    print(f"✅ Created {SubscriptionPlan.objects.count()} subscription plans:")
    for plan in SubscriptionPlan.objects.all():
        print(f"  - {plan.display_name}: {plan.price_monthly:,.0f} {plan.currency}/month")

if __name__ == '__main__':
    create_subscription_plans()