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
