from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class NotificationEmailService:
    """Service for sending notification emails"""
    
    @staticmethod
    def send_notification_email(notification, dry_run=False):
        """
        Send notification email to target users
        
        Args:
            notification: SystemNotification instance
            dry_run: If True, only return count without sending emails
            
        Returns:
            dict with success status and stats
        """
        try:
            # Get target users
            target_users = notification.get_target_users_queryset()
            user_count = target_users.count()
            
            if dry_run:
                return {
                    'success': True,
                    'message': f'Would send to {user_count} users',
                    'recipient_count': user_count,
                    'sent_count': 0
                }
            
            if user_count == 0:
                return {
                    'success': False,
                    'message': 'No users found matching the target criteria',
                    'recipient_count': 0,
                    'sent_count': 0
                }
            
            # Prepare email content
            subject = notification.email_subject or notification.title
            
            # Prepare email context
            email_context = {
                'notification': notification,
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.get_notification_type_display(),
                'created_by': notification.created_by.get_full_name() or notification.created_by.username,
                'created_at': notification.created_at,
            }
            
            # Render email templates
            html_message = render_to_string('emails/notification_email.html', email_context)
            text_message = render_to_string('emails/notification_email.txt', email_context)
            
            # Update notification status
            notification.email_status = 'sending'
            notification.save()
            
            # Send emails in batches to avoid overwhelming the email service
            batch_size = 50
            sent_count = 0
            failed_count = 0
            
            for i in range(0, user_count, batch_size):
                batch_users = target_users[i:i + batch_size]
                
                for user in batch_users:
                    if user.email:
                        try:
                            # Personalize context for each user
                            user_context = email_context.copy()
                            user_context.update({
                                'user': user,
                                'user_name': user.get_full_name() or user.username,
                            })
                            
                            # Re-render with user context
                            user_html_message = render_to_string('emails/notification_email.html', user_context)
                            user_text_message = render_to_string('emails/notification_email.txt', user_context)
                            
                            # Create email with HTML content
                            email = EmailMultiAlternatives(
                                subject=subject,
                                body=user_text_message,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                to=[user.email]
                            )
                            email.attach_alternative(user_html_message, "text/html")
                            
                            # Send email
                            email.send(fail_silently=False)
                            sent_count += 1
                            logger.info(f"Sent notification email to {user.email}")
                            
                        except Exception as e:
                            failed_count += 1
                            logger.error(f"Failed to send notification email to {user.email}: {str(e)}")
                            continue
            
            # Update notification with results
            notification.emails_sent = sent_count
            notification.email_sent_at = timezone.now()
            notification.email_status = 'sent' if failed_count == 0 else 'failed'
            notification.save()
            
            if sent_count > 0:
                return {
                    'success': True,
                    'message': f'Successfully sent emails to {sent_count} users' + 
                              (f' ({failed_count} failed)' if failed_count > 0 else ''),
                    'recipient_count': user_count,
                    'sent_count': sent_count,
                    'failed_count': failed_count
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to send emails to all {user_count} users',
                    'recipient_count': user_count,
                    'sent_count': 0,
                    'failed_count': failed_count
                }
                
        except Exception as e:
            logger.error(f"Error sending notification email: {str(e)}")
            notification.email_status = 'failed'
            notification.save()
            
            return {
                'success': False,
                'message': f'Error sending emails: {str(e)}',
                'recipient_count': 0,
                'sent_count': 0
            }
    
    @staticmethod
    def preview_notification_email(notification):
        """
        Generate a preview of the notification email
        
        Args:
            notification: SystemNotification instance
            
        Returns:
            dict with email preview content
        """
        try:
            # Create sample user for preview
            sample_user = User.objects.first()
            if not sample_user:
                sample_user = User(
                    username='sample_user',
                    first_name='John',
                    last_name='Doe',
                    email='sample@photographers.rw'
                )
            
            email_context = {
                'notification': notification,
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.get_notification_type_display(),
                'created_by': notification.created_by.get_full_name() or notification.created_by.username,
                'created_at': notification.created_at,
                'user': sample_user,
                'user_name': sample_user.get_full_name() or sample_user.username,
            }
            
            subject = notification.email_subject or notification.title
            html_content = render_to_string('emails/notification_email.html', email_context)
            text_content = render_to_string('emails/notification_email.txt', email_context)
            
            return {
                'success': True,
                'subject': subject,
                'html_content': html_content,
                'text_content': text_content,
                'recipient_count': notification.get_recipients_count()
            }
            
        except Exception as e:
            logger.error(f"Error generating email preview: {str(e)}")
            return {
                'success': False,
                'message': f'Error generating preview: {str(e)}'
            }
    
    @staticmethod
    def generate_preview_html(notification):
        """
        Generate HTML preview for email template with both HTML and text versions
        
        Args:
            notification: SystemNotification instance
            
        Returns:
            str: HTML content for preview modal
        """
        try:
            # Create sample user for preview
            sample_user = User.objects.first()
            if not sample_user:
                sample_user = User(
                    username='sample_user',
                    first_name='John',
                    last_name='Doe',
                    email='sample@photographers.rw'
                )
            
            email_context = {
                'notification': notification,
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.get_notification_type_display(),
                'created_by': getattr(notification.created_by, 'get_full_name', lambda: 'Admin')() or 'Admin',
                'created_at': getattr(notification, 'created_at', timezone.now()),
                'user': sample_user,
                'user_name': sample_user.get_full_name() or sample_user.username,
            }
            
            subject = notification.email_subject or notification.title
            html_content = render_to_string('emails/notification_email.html', email_context)
            text_content = render_to_string('emails/notification_email.txt', email_context)
            
            # Get recipient count
            try:
                recipient_count = notification.get_target_users_queryset().count()
            except:
                recipient_count = 0
            
            # Generate preview HTML with tabs for HTML and text versions
            preview_html = f"""
            <div class="email-preview">
                <div class="row mb-3">
                    <div class="col-md-8">
                        <h6><strong>Subject:</strong> {subject}</h6>
                        <p class="text-muted mb-0"><strong>Recipients:</strong> {recipient_count} users</p>
                    </div>
                    <div class="col-md-4 text-end">
                        <small class="text-muted">Preview with sample user data</small>
                    </div>
                </div>
                
                <!-- Email Content Tabs -->
                <ul class="nav nav-tabs" id="emailPreviewTabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="html-tab" data-bs-toggle="tab" data-bs-target="#html-content" 
                                type="button" role="tab" aria-controls="html-content" aria-selected="true">
                            HTML Version
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="text-tab" data-bs-toggle="tab" data-bs-target="#text-content" 
                                type="button" role="tab" aria-controls="text-content" aria-selected="false">
                            Text Version
                        </button>
                    </li>
                </ul>
                
                <div class="tab-content" id="emailPreviewTabsContent">
                    <div class="tab-pane fade show active" id="html-content" role="tabpanel" aria-labelledby="html-tab">
                        <div class="border rounded p-3 mt-3" style="max-height: 400px; overflow-y: auto;">
                            {html_content}
                        </div>
                    </div>
                    <div class="tab-pane fade" id="text-content" role="tabpanel" aria-labelledby="text-tab">
                        <div class="border rounded p-3 mt-3" style="max-height: 400px; overflow-y: auto;">
                            <pre class="mb-0" style="white-space: pre-wrap; font-family: monospace;">{text_content}</pre>
                        </div>
                    </div>
                </div>
            </div>
            """
            
            return preview_html
            
        except Exception as e:
            logger.error(f"Error generating preview HTML: {str(e)}")
            return f"""
            <div class="alert alert-danger">
                <h6>Error generating preview</h6>
                <p class="mb-0">Error: {str(e)}</p>
            </div>
            """