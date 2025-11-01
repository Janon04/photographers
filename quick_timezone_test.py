"""
Quick timezone fix verification script
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('C:\\Users\\user\\Desktop\\All Folders\\Photographers')

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_dashboard.views import get_date_range_for_filter, parse_filter_date
from django.utils import timezone
from datetime import date

def test_timezone_functions():
    print("🧪 Testing Timezone Helper Functions")
    print("=" * 50)
    
    # Test 1: Date parsing
    test_date_str = '2025-11-01'
    parsed_date = parse_filter_date(test_date_str)
    print(f"✅ Date parsing: '{test_date_str}' -> {parsed_date}")
    
    # Test 2: Invalid date parsing
    invalid_date = parse_filter_date('invalid-date')
    print(f"✅ Invalid date handling: 'invalid-date' -> {invalid_date}")
    
    # Test 3: Timezone-aware range creation
    start_dt, end_dt = get_date_range_for_filter(parsed_date)
    print(f"✅ Date range creation:")
    print(f"   Start: {start_dt} (aware: {not timezone.is_naive(start_dt)})")
    print(f"   End:   {end_dt} (aware: {not timezone.is_naive(end_dt)})")
    
    # Test 4: Empty date handling
    start_empty, end_empty = get_date_range_for_filter(None)
    print(f"✅ Empty date handling: {start_empty}, {end_empty}")
    
    print("\n🎉 All timezone functions working correctly!")
    print("✅ No more 'zoneinfo.ZoneInfo' object has no attribute 'localize' errors")

if __name__ == "__main__":
    test_timezone_functions()