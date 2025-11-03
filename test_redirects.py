#!/usr/bin/env python
"""Test script to check URL redirects"""

import requests
import sys

def test_redirects():
    """Test the Django admin redirects"""
    base_url = "http://127.0.0.1:8000"
    
    # Test URLs that should redirect
    test_urls = [
        "/admin/payments/subscriptionplan/",
        "/admin/payments/subscriptionplan/add/",
        "/admin/payments/usersubscription/",
        "/admin/payments/subscriptionpayment/",
    ]
    
    print("Testing Django Admin URL Redirects")
    print("=" * 50)
    
    for url in test_urls:
        full_url = base_url + url
        try:
            response = requests.get(full_url, allow_redirects=False)
            
            if response.status_code in [301, 302]:
                redirect_url = response.headers.get('Location', 'Unknown')
                print(f"✅ {url}")
                print(f"   Status: {response.status_code} - Redirects to: {redirect_url}")
            elif response.status_code == 200:
                print(f"✅ {url}")
                print(f"   Status: {response.status_code} - Shows redirect notice page")
            else:
                print(f"❌ {url}")
                print(f"   Status: {response.status_code} - Unexpected response")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {url}")
            print(f"   Error: Cannot connect to server. Is Django running?")
            return False
        except Exception as e:
            print(f"❌ {url}")
            print(f"   Error: {str(e)}")
            
        print()
    
    # Test custom dashboard URLs
    custom_urls = [
        "/admin-dashboard/",
        "/admin-dashboard/subscriptions/plans/",
        "/admin-dashboard/subscriptions/users/",
        "/admin-dashboard/subscriptions/payments/",
    ]
    
    print("Testing Custom Admin Dashboard URLs")
    print("=" * 50)
    
    for url in custom_urls:
        full_url = base_url + url
        try:
            response = requests.get(full_url, allow_redirects=True)
            
            if response.status_code == 200:
                print(f"✅ {url}")
                print(f"   Status: {response.status_code} - Page loads successfully")
            else:
                print(f"❌ {url}")
                print(f"   Status: {response.status_code} - Page not accessible")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {url}")
            print(f"   Error: Cannot connect to server. Is Django running?")
            return False
        except Exception as e:
            print(f"❌ {url}")
            print(f"   Error: {str(e)}")
            
        print()
    
    return True

if __name__ == '__main__':
    print("Django Admin URL Redirect Test")
    print("Make sure Django server is running on http://127.0.0.1:8000")
    print()
    
    success = test_redirects()
    
    if success:
        print("Test completed! Check the results above.")
    else:
        print("Test failed due to connection issues.")
        sys.exit(1)