"""
Test script for Help Center email notifications
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('c:\\Users\\user\\Desktop\\All Folders\\Photographers')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from helpcenter.models import UserQuestion
from config.email_service import EmailService

def test_help_center_email():
    """Test the help center email notification"""
    print("Testing Help Center Email Notifications...")
    
    # Create a test question
    test_question = UserQuestion.objects.create(
        name="Test User",
        email="test@example.com",  # Use a test email
        question="This is a test question to verify email notifications are working properly."
    )
    
    print(f"Created test question #{test_question.id}")
    
    # Send email notifications
    try:
        success = EmailService.send_help_question_notification(test_question)
        if success:
            print("✅ Email notifications sent successfully!")
            print(f"   - User confirmation sent to: {test_question.email}")
            print(f"   - Admin notification sent to admins")
        else:
            print("❌ Failed to send email notifications")
    except Exception as e:
        print(f"❌ Error sending email notifications: {e}")
    
    # Clean up test data
    test_question.delete()
    print("Test question cleaned up")

if __name__ == "__main__":
    test_help_center_email()