#!/usr/bin/env python
"""
Debug email sending issues
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from admin_dashboard.models import SystemNotification
from admin_dashboard.email_service import NotificationEmailService
from django.contrib.auth import get_user_model

User = get_user_model()

def debug_email_sending():
    """Debug email sending issues"""
    print("🔍 Debugging Email Sending Issues")
    print("=" * 50)
    
    # Check email settings
    print("📧 Email Configuration:")
    print(f"   • Backend: {settings.EMAIL_BACKEND}")
    print(f"   • Host: {settings.EMAIL_HOST}")
    print(f"   • Port: {settings.EMAIL_PORT}")
    print(f"   • TLS: {settings.EMAIL_USE_TLS}")
    print(f"   • User: {settings.EMAIL_HOST_USER}")
    print(f"   • Password: {'Set' if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
    print(f"   • From Email: {settings.DEFAULT_FROM_EMAIL}")
    
    # Check users
    print(f"\n👥 Users Analysis:")
    users = User.objects.filter(is_active=True)
    print(f"   • Total active users: {users.count()}")
    
    for user in users:
        print(f"   • {user.email} ({user.role}) - Active: {user.is_active}")
    
    # Test basic email sending
    print(f"\n🧪 Testing Basic Email...")
    try:
        result = send_mail(
            'Test Email',
            'This is a test email.',
            settings.DEFAULT_FROM_EMAIL,
            ['test@example.com'],
            fail_silently=False,
        )
        print(f"✅ Basic email test result: {result}")
    except Exception as e:
        print(f"❌ Basic email test failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        
        # Common email errors
        if "authentication" in str(e).lower():
            print("   💡 This appears to be an authentication issue")
            print("   💡 Check EMAIL_HOST_PASSWORD environment variable")
        elif "connection" in str(e).lower():
            print("   💡 This appears to be a connection issue")
            print("   💡 Check internet connection and SMTP settings")
        elif "recipients" in str(e).lower():
            print("   💡 This appears to be a recipient issue")
    
    # Test notification email service
    print(f"\n📨 Testing Notification Email Service...")
    
    # Create a test notification
    admin_user = User.objects.filter(role='admin').first()
    if not admin_user:
        print("❌ No admin user found for testing")
        return
    
    try:
        # Create test notification (don't save to DB)
        test_notification = SystemNotification(
            title="Test Email Notification",
            message="This is a test email from the notification system",
            notification_type="info",
            target_users="all",
            delivery_method="email",
            email_subject="Test Email Subject",
            created_by=admin_user
        )
        
        # Test the email service with dry run
        email_service = NotificationEmailService()
        result = email_service.send_notification_email(test_notification, dry_run=True)
        
        print(f"✅ Dry run result: {result}")
        
        if result['success']:
            print(f"   • Would send to {result['recipient_count']} users")
        else:
            print(f"   • Error: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Notification service test failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
    
    print(f"\n💡 Recommendations:")
    if not settings.EMAIL_HOST_PASSWORD:
        print("   • Set EMAIL_HOST_PASSWORD environment variable")
        print("   • For Gmail, use an App Password (not regular password)")
        print("   • Or switch to console backend for testing:")
        print("     EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'")
    
    print("   • Check that users have valid email addresses")
    print("   • Verify SMTP settings are correct")

if __name__ == "__main__":
    debug_email_sending()