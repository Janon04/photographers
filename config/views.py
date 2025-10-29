# Homepage views for the project
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages

def home(request):
    # Import models here to avoid circular imports
    from portfolio.models import Story, Photo
    from community.models import Post
    from django.utils import timezone
    from django.db.models import Count, Q
    # Get all active stories (last 24h)
    time_threshold = timezone.now() - timezone.timedelta(hours=24)
    stories = Story.objects.filter(created_at__gte=time_threshold).order_by('-created_at')
    # Get recent photos
    photos = Photo.objects.all().order_by('-uploaded_at')[:12]
    # Get recent community posts
    posts = Post.objects.all().order_by('-date')[:6]
    # Featured photos: top 6 approved photos by like count
    featured_photos = Photo.objects.filter(is_approved=True).annotate(
        num_likes=Count('likes', filter=Q(likes__is_like=True))
    ).order_by('-num_likes', '-uploaded_at')[:6]
    return render(request, 'home.html', {
        'stories': stories,
        'photos': photos,
        'posts': posts,
        'featured_photos': featured_photos,
    })
    
from portfolio.models import PrivacyPolicy, TermsOfService

def privacy_policy(request):
    policy = PrivacyPolicy.objects.order_by('-updated_at').first()
    return render(request, 'privacy_policy.html', {'policy': policy})

def terms_of_service(request):
    terms = TermsOfService.objects.order_by('-updated_at').first()
    return render(request, 'terms_of_service.html', {'terms': terms})

from django.core.mail import send_mail
from django.conf import settings

def contact_us(request):
    success = False
    error_message = None
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()
        
        print(f"📧 Contact form submission: {name} ({email})")  # Debug log
        
        # Basic validation
        if not name or not email or not message:
            error_message = "All fields are required. Please fill out all fields."
        elif len(name) < 2:
            error_message = "Name must be at least 2 characters long."
        elif len(message) < 10:
            error_message = "Message must be at least 10 characters long."
        else:
            try:
                # Save to database
                from portfolio.models import ContactMessage
                contact_msg = ContactMessage.objects.create(
                    name=name, 
                    email=email, 
                    message=message
                )
                print(f"💾 Message saved to database: ID {contact_msg.id}")
                
                # Prepare email context for HTML templates
                email_context = {
                    'contact_name': name,
                    'contact_email': email,
                    'message_content': message,
                    'submitted_at': contact_msg.submitted_at,
                    'message_id': contact_msg.id,
                    'site_url': 'http://127.0.0.1:8000'  # Update this for production
                }
                
                # Send notification email to admin using HTML template
                try:
                    from django.template.loader import render_to_string
                    from django.core.mail import EmailMultiAlternatives
                    
                    print("📤 Sending admin notification email...")
                    
                    # Render HTML email template
                    admin_html_content = render_to_string('emails/contact_admin_notification.html', email_context)
                    admin_text_content = f"""
New contact form submission from {name}

Name: {name}
Email: {email}
Message: {message}
Submitted: {contact_msg.submitted_at.strftime('%Y-%m-%d at %H:%M')}

Reply to: {email}
                    """
                    
                    # Create email with HTML content
                    admin_email = EmailMultiAlternatives(
                        subject=f"New Contact Form Submission from {name} - PhotoRw",
                        body=admin_text_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[settings.DEFAULT_FROM_EMAIL],
                    )
                    admin_email.attach_alternative(admin_html_content, "text/html")
                    admin_result = admin_email.send()
                    print(f"✅ Admin email sent successfully: {admin_result}")
                    
                    # Send confirmation email to user using HTML template
                    print("📤 Sending user confirmation email...")
                    
                    user_html_content = render_to_string('emails/contact_user_confirmation.html', email_context)
                    user_text_content = f"""
Dear {name},

Thank you for contacting PhotoRw! We have received your message and will get back to you soon.

Your message: {message}

We typically respond within 24-48 hours.

Best regards,
The PhotoRw Team
                    """
                    
                    user_email = EmailMultiAlternatives(
                        subject="Thank you for contacting PhotoRw! 🙏",
                        body=user_text_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[email],
                    )
                    user_email.attach_alternative(user_html_content, "text/html")
                    user_result = user_email.send(fail_silently=True)
                    print(f"✅ User confirmation email sent: {user_result}")
                    
                except Exception as email_error:
                    # Log the error but don't fail the form submission
                    print(f"❌ Email sending failed: {email_error}")
                    import traceback
                    traceback.print_exc()
                    # Still consider it a success since the message was saved
                
                success = True
                messages.success(request, f"Thank you, {name}! Your message has been sent successfully. We'll get back to you soon.")
                print(f"🎉 Contact form submission completed successfully")
                
                # Redirect to avoid form resubmission
                return redirect('contact_us')
                
            except Exception as e:
                error_message = f"An error occurred while sending your message. Please try again."
                print(f"❌ Contact form error: {e}")
                import traceback
                traceback.print_exc()
    
    return render(request, 'contact_us.html', {
        'success': success,
        'error_message': error_message
    })
