# Homepage views for the project
from django.shortcuts import render

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
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        # Save to database
        from portfolio.models_contact import ContactMessage
        ContactMessage.objects.create(name=name, email=email, message=message)
        # Send email (customize recipient as needed)
        send_mail(
            subject=f"Contact Us Message from {name}",
            message=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
            fail_silently=True,
        )
        success = True
    return render(request, 'contact_us.html', {'success': success})
