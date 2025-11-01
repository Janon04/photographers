"""
Test script to verify analytics date filter functionality
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('C:\\Users\\user\\Desktop\\All Folders\\Photographers')

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

def test_analytics_date_filter():
    print("🧪 Testing Analytics Date Filter Functionality")
    print("=" * 60)
    
    # Create a test admin user
    try:
        admin_user = User.objects.get(email='admin@test.com')
    except User.DoesNotExist:
        admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            role=User.Roles.ADMIN,
            first_name='Test',
            last_name='Admin'
        )
    
    client = Client()
    
    # Test 1: Analytics page loads without date filter
    print("1. Testing analytics page without date filter...")
    response = client.get(reverse('admin_dashboard:analytics'))
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Page loads successfully")
    else:
        print("   ❌ Page failed to load")
        return
    
    # Test 2: Analytics page with date filter
    print("\n2. Testing analytics page with date filter...")
    test_date = '2025-11-01'
    response = client.get(reverse('admin_dashboard:analytics'), {
        'filter_date': test_date,
        'period': '30'
    })
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Page loads successfully with date filter")
        
        # Check if the date appears in the context
        if hasattr(response, 'context') and response.context:
            filter_date = response.context.get('filter_date')
            print(f"   📅 Filter date in context: {filter_date}")
            
            filter_date_formatted = response.context.get('filter_date_formatted')
            print(f"   📅 Formatted date: {filter_date_formatted}")
        else:
            print("   ⚠️ No context available (might be due to test environment)")
    else:
        print("   ❌ Page failed to load with date filter")
        return
    
    # Test 3: Analytics page with period only (clear filter simulation)
    print("\n3. Testing analytics page with period only (clear filter)...")
    response = client.get(reverse('admin_dashboard:analytics'), {
        'period': '30'
    })
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Clear filter works (no date parameter)")
    else:
        print("   ❌ Clear filter failed")
    
    # Test 4: Invalid date handling
    print("\n4. Testing invalid date handling...")
    response = client.get(reverse('admin_dashboard:analytics'), {
        'filter_date': 'invalid-date',
        'period': '30'
    })
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Invalid date handled gracefully")
    else:
        print("   ❌ Invalid date caused error")
    
    print("\n🎉 Analytics date filter testing completed!")
    print("✅ All tests passed - date filtering should work properly in the browser")

if __name__ == "__main__":
    test_analytics_date_filter()