#!/usr/bin/env python3
"""
Demo script for the Photography Platform Subscription System
This script demonstrates the key features of the subscription system.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from payments.models import SubscriptionPlan, UserSubscription
from payments.services import SubscriptionService

User = get_user_model()

def demo_subscription_system():
    """Demonstrate the subscription system functionality"""
    
    print("🎯 Photography Platform - Subscription System Demo")
    print("=" * 50)
    
    # 1. Show available plans
    print("\n📋 Available Subscription Plans:")
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price_monthly')
    for plan in plans:
        print(f"  💎 {plan.display_name}")
        print(f"     Price: {plan.price_monthly:,.0f} RWF/month")
        print(f"     Commission: {plan.commission_rate}%")
        print(f"     Photos: {plan.max_photos_upload if plan.max_photos_upload != -1 else 'Unlimited'}")
        print(f"     Storage: {plan.max_storage_gb if plan.max_storage_gb != -1 else 'Unlimited'} GB")
        print()
    
    # 2. Create a demo user if needed
    demo_user, created = User.objects.get_or_create(
        username='demo_photographer',
        defaults={
            'email': 'demo@photographer.com',
            'first_name': 'Demo',
            'last_name': 'Photographer',
            'role': 'photographer'
        }
    )
    
    if created:
        print(f"✅ Created demo user: {demo_user.username}")
    else:
        print(f"👤 Using existing demo user: {demo_user.username}")
    
    # 3. Get or create subscription
    subscription = SubscriptionService.get_or_create_user_subscription(demo_user)
    print(f"\n📊 Current Subscription:")
    print(f"   Plan: {subscription.plan.display_name}")
    print(f"   Status: {subscription.get_status_display()}")
    print(f"   Commission Rate: {subscription.plan.commission_rate}%")
    
    # 4. Show usage tracking
    print(f"\n📈 Usage This Month:")
    print(f"   Photos uploaded: {subscription.photos_uploaded_this_month}/{subscription.plan.max_photos_upload if subscription.plan.max_photos_upload != -1 else 'Unlimited'}")
    print(f"   Storage used: {subscription.storage_used_gb} GB/{subscription.plan.max_storage_gb if subscription.plan.max_storage_gb != -1 else 'Unlimited'} GB")
    print(f"   Bookings: {subscription.bookings_this_month}/{subscription.plan.max_bookings_per_month if subscription.plan.max_bookings_per_month != -1 else 'Unlimited'}")
    
    # 5. Demonstrate usage limit checking
    print(f"\n🔍 Testing Usage Limits:")
    can_upload, message = SubscriptionService.check_usage_limits(demo_user, 'upload_photos', 5)
    print(f"   Can upload 5 photos? {can_upload} - {message}")
    
    can_book, message = SubscriptionService.check_usage_limits(demo_user, 'create_booking')
    print(f"   Can create booking? {can_book} - {message}")
    
    # 6. Demonstrate subscription upgrade
    if subscription.plan.name == 'basic':
        print(f"\n🚀 Upgrading to Standard Plan:")
        try:
            new_subscription, prorated_amount = SubscriptionService.upgrade_subscription(
                demo_user, 'standard', 'monthly'
            )
            print(f"   ✅ Successfully upgraded to {new_subscription.plan.display_name}")
            print(f"   💰 New commission rate: {new_subscription.plan.commission_rate}%")
            print(f"   💳 Prorated amount: {prorated_amount:.2f} RWF")
        except Exception as e:
            print(f"   ❌ Upgrade failed: {str(e)}")
    
    print(f"\n🎉 Demo completed! Visit the admin panel or web interface to explore more features.")
    print(f"\n📱 Web Interface URLs:")
    print(f"   Pricing Page: /payments/pricing/")
    print(f"   Subscription Dashboard: /payments/subscription/")
    print(f"   Billing History: /payments/billing/")
    print(f"\n🔧 Admin Interface:")
    print(f"   Admin Dashboard: /admin/")
    print(f"   Subscription Plans: /admin/payments/subscriptionplan/")
    print(f"   User Subscriptions: /admin/payments/usersubscription/")

if __name__ == "__main__":
    demo_subscription_system()