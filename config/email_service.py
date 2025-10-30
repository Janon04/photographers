"""
Email service for PhotoRw platform
Handles all email notifications professionally
"""
import logging
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.models import Site

logger = logging.getLogger(__name__)

class EmailService:
    """Professional email service for PhotoRw platform"""
    
    @staticmethod
    def get_base_url():
        """Get the base URL for email links"""
        try:
            site = Site.objects.get_current()
            return f"http://{site.domain}"
        except:
            return "http://127.0.0.1:8000"  # Fallback for development
    
    @staticmethod
    def send_activation_email(user, request=None):
        """Send professional account activation email"""
        try:
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes
            from django.contrib.auth.tokens import default_token_generator
            
            # Generate activation link
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            if request:
                activation_link = request.build_absolute_uri(f"/users/activate/{uid}/{token}/")
            else:
                base_url = EmailService.get_base_url()
                activation_link = f"{base_url}/users/activate/{uid}/{token}/"
            
            # Render email content
            html_content = render_to_string('emails/activation_email.html', {
                'user': user,
                'activation_link': activation_link,
            })
            
            text_content = f"""
Welcome to PhotoRw!

Hello {user.get_full_name() or user.username},

Thank you for joining Rwanda's premier photography platform!

To activate your account, please visit:
{activation_link}

This link will expire in 24 hours for security.

Welcome to the PhotoRw family!

Best regards,
The PhotoRw Team
            """.strip()
            
            # Send email
            success = send_mail(
                subject='Welcome to PhotoRw - Activate Your Account',
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content,
                fail_silently=True
            )
            
            if success:
                logger.info(f"Activation email sent successfully to {user.email}")
            else:
                logger.warning(f"Failed to send activation email to {user.email}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending activation email to {user.email}: {e}")
            return False
    
    @staticmethod
    def send_payment_notification(transaction, status='success'):
        """Send payment notification email"""
        try:
            user = transaction.user
            booking = transaction.booking
            
            # Determine retry link for failed payments
            retry_payment_link = None
            if status == 'failed':
                base_url = EmailService.get_base_url()
                retry_payment_link = f"{base_url}/payments/retry/{transaction.id}/"
            
            # Render email content
            html_content = render_to_string('emails/payment_notification.html', {
                'user': user,
                'transaction': transaction,
                'booking': booking,
                'status': status,
                'retry_payment_link': retry_payment_link,
            })
            
            text_content = f"""
Payment {status.title()} - PhotoRw

Hello {user.get_full_name() or user.username},

{'Your payment has been processed successfully!' if status == 'success' else 'Your payment could not be processed.'}

Transaction Details:
- Transaction ID: {transaction.transaction_id}
- Amount: ${transaction.amount}
- Payment Method: {transaction.payment_method}
- Service: {booking.service_type}
- Photographer: {booking.photographer.get_full_name()}

{'Your booking is now confirmed!' if status == 'success' else 'Please try again or contact support.'}

Best regards,
The PhotoRw Team
            """.strip()
            
            subject = f"Payment {'Successful' if status == 'success' else 'Failed'} - PhotoRw"
            
            success = send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content,
                fail_silently=True
            )
            
            if success:
                logger.info(f"Payment {status} notification sent to {user.email}")
            else:
                logger.warning(f"Failed to send payment {status} notification to {user.email}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending payment notification: {e}")
            return False
    
    @staticmethod
    def send_booking_notification(booking, action='confirmed', recipient=None):
        """Send booking notification email"""
        try:
            # Determine recipient
            if recipient == 'photographer':
                user = booking.photographer
                email = booking.photographer.email
                user_name = booking.photographer.get_full_name() or booking.photographer.username
            else:
                # For client notifications
                if booking.client:
                    user = booking.client
                    email = booking.client.email
                    user_name = booking.client.get_full_name() or booking.client.username
                else:
                    user = None
                    email = booking.client_email
                    user_name = booking.client_name or 'Valued Client'
            
            # Generate action-specific links
            base_url = EmailService.get_base_url()
            review_link = f"{base_url}/reviews/add/?booking={booking.id}"
            booking_link = f"{base_url}/bookings/create/"
            
            # Render email content
            html_content = render_to_string('emails/booking_notification.html', {
                'user': user,
                'user_name': user_name,
                'booking': booking,
                'action': action,
                'review_link': review_link,
                'booking_link': booking_link,
            })
            
            text_content = f"""
Booking {action.title()} - PhotoRw

Hello {user_name},

Your booking has been {action}.

Booking Details:
- Booking ID: #{booking.id}
- Service: {booking.service_type}
- Date & Time: {booking.date} at {booking.time}
- Location: {booking.location}
- Photographer: {booking.photographer.get_full_name()}
- Status: {booking.get_status_display()}

Thank you for using PhotoRw!

Best regards,
The PhotoRw Team
            """.strip()
            
            subject = f"Booking {action.title()} - PhotoRw"
            
            success = send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_content,
                fail_silently=True
            )
            
            if success:
                logger.info(f"Booking {action} notification sent to {email}")
            else:
                logger.warning(f"Failed to send booking {action} notification to {email}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending booking notification: {e}")
            return False
    
    @staticmethod
    def send_review_notification(review):
        """Send review notification to photographer"""
        try:
            photographer = review.photographer
            
            html_content = render_to_string('emails/review_notification.html', {
                'photographer': photographer,
                'review': review,
                'reviewer': review.reviewer,
            })
            
            text_content = f"""
New Review Received - PhotoRw

Hello {photographer.get_full_name()},

You have received a new review!

Reviewer: {review.reviewer.get_full_name()}
Rating: {review.rating}/5 stars
Comment: "{review.comment}"

Thank you for providing excellent service!

Best regards,
The PhotoRw Team
            """.strip()
            
            success = send_mail(
                subject='New Review Received - PhotoRw',
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[photographer.email],
                html_message=html_content,
                fail_silently=True
            )
            
            if success:
                logger.info(f"Review notification sent to {photographer.email}")
            else:
                logger.warning(f"Failed to send review notification to {photographer.email}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending review notification: {e}")
            return False
    
    @staticmethod
    def send_help_question_notification(user_question):
        """Send notification when a new help question is submitted"""
        try:
            # Send confirmation email to the user
            user_html_content = render_to_string('emails/help_user_confirmation.html', {
                'user_question': user_question,
                'base_url': EmailService.get_base_url(),
            })
            
            user_text_content = f"""
Dear {user_question.name or 'User'},

Thank you for contacting PhotoRw Help Center!

════════════════════════════════════════════════════════════════
📝 YOUR QUESTION:
════════════════════════════════════════════════════════════════

{user_question.question}

════════════════════════════════════════════════════════════════

Our support team will review your question and respond as soon as possible. You can expect a response within 24-48 hours during business days.

Question Details:
- Submitted: {user_question.submitted_at.strftime('%B %d, %Y at %I:%M %p')}
- Reference ID: #{user_question.id}

Best regards,
PhotoRw Support Team
            """.strip()
            
            # Send confirmation to user
            user_success = send_mail(
                subject='Your Question Has Been Received - PhotoRw Help Center',
                message=user_text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_question.email] if user_question.email else [],
                html_message=user_html_content,
                fail_silently=True
            )
            
            # Send notification to admin
            admin_html_content = render_to_string('emails/help_admin_notification.html', {
                'user_question': user_question,
                'admin_url': f"{EmailService.get_base_url()}/admin/helpcenter/userquestion/{user_question.id}/change/",
            })
            
            admin_text_content = f"""
New Help Center Question Received

From: {user_question.name or 'Anonymous'} ({user_question.email or 'No email provided'})
Submitted: {user_question.submitted_at.strftime('%B %d, %Y at %I:%M %p')}

════════════════════════════════════════════════════════════════
❓ USER'S QUESTION:
════════════════════════════════════════════════════════════════

{user_question.question}

════════════════════════════════════════════════════════════════

View in admin panel: {EmailService.get_base_url()}/admin/helpcenter/userquestion/{user_question.id}/change/

Best regards,
PhotoRw System
            """.strip()
            
            # Get admin emails from settings or use default
            admin_emails = getattr(settings, 'ADMIN_EMAILS', [settings.DEFAULT_FROM_EMAIL])
            
            admin_success = send_mail(
                subject='New Help Center Question - PhotoRw',
                message=admin_text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                html_message=admin_html_content,
                fail_silently=True
            )
            
            if user_success:
                logger.info(f"Help question confirmation sent to {user_question.email}")
            if admin_success:
                logger.info(f"Help question notification sent to admins")
                
            return user_success or admin_success
            
        except Exception as e:
            logger.error(f"Error sending help question notification: {e}")
            return False
    
    @staticmethod
    def send_help_response_notification(user_question):
        """Send notification when admin responds to a help question"""
        try:
            if not user_question.email or not user_question.admin_response:
                logger.warning(f"Cannot send response email for question #{user_question.id}: missing email or response")
                return False
            
            # Send response email to the user
            response_html_content = render_to_string('emails/help_response_notification.html', {
                'user_question': user_question,
                'base_url': EmailService.get_base_url(),
            })
            
            response_text_content = f"""
Dear {user_question.name or 'User'},

We have responded to your question submitted to PhotoRw Help Center!

════════════════════════════════════════════════════════════════
📝 YOUR ORIGINAL QUESTION:
════════════════════════════════════════════════════════════════

{user_question.question}

════════════════════════════════════════════════════════════════
✅ OUR RESPONSE:
════════════════════════════════════════════════════════════════

{user_question.admin_response}

════════════════════════════════════════════════════════════════

Question Details:
- Original Submission: {user_question.submitted_at.strftime('%B %d, %Y at %I:%M %p')}
- Response Date: {user_question.responded_at.strftime('%B %d, %Y at %I:%M %p') if user_question.responded_at else 'Just now'}
- Reference ID: #{user_question.id}
- Responded by: {user_question.responded_by.get_full_name() if user_question.responded_by else 'PhotoRw Support Team'}

If you have any follow-up questions, please don't hesitate to contact us again at {EmailService.get_base_url()}/help/

Thank you for choosing PhotoRw!

Best regards,
PhotoRw Support Team
            """.strip()
            
            # Send response to user
            user_success = send_mail(
                subject='Response to Your Question - PhotoRw Help Center',
                message=response_text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_question.email],
                html_message=response_html_content,
                fail_silently=True
            )
            
            if user_success:
                logger.info(f"Help response email sent to {user_question.email} for question #{user_question.id}")
            else:
                logger.warning(f"Failed to send help response email to {user_question.email}")
                
            return user_success
            
        except Exception as e:
            logger.error(f"Error sending help response notification: {e}")
            return False