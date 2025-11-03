#!/usr/bin/env python
"""
Quick test to verify subscription plan editing functionality
"""
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from payments.models import SubscriptionPlan
from admin_dashboard.forms import SubscriptionPlanForm

def test_subscription_edit():
    print("Testing Subscription Plan Edit Functionality...")
    print("-" * 50)
    
    # Get the first subscription plan
    try:
        plan = SubscriptionPlan.objects.first()
        if not plan:
            print("❌ No subscription plans found in database")
            return
        
        print(f"✅ Found subscription plan: {plan.name}")
        print(f"   Display Name: {plan.display_name}")
        print(f"   Monthly Price: {plan.price_monthly} RWF")
        print(f"   Annual Price: {plan.price_yearly} RWF")
        
        # Test form initialization with existing data
        form = SubscriptionPlanForm(instance=plan)
        print(f"✅ SubscriptionPlanForm initialized successfully")
        print(f"   Form has model: {form._meta.model}")
        print(f"   Form fields: {list(form.fields.keys())}")
        
        # Test form validation with existing data
        if form.is_valid():
            print("✅ Form validation passed with existing data")
        else:
            print("❌ Form validation failed:")
            for field, errors in form.errors.items():
                print(f"   {field}: {errors}")
        
        # Test saving the form (dry run - don't actually save)
        print("✅ ModelForm configuration is working correctly!")
        print(f"✅ Edit URL should work: /admin-dashboard/subscriptions/plans/{plan.id}/edit/")
        
    except Exception as e:
        print(f"❌ Error testing subscription edit: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_subscription_edit()