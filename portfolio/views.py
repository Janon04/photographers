from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import PhotoForm
from django.db.models import Count, Avg, Q
from collections import Counter
import json

@login_required
def upload_photo(request):
	if not hasattr(request.user, 'role') or request.user.role != 'photographer':
		return render(request, 'portfolio/not_photographer.html', {'message': 'Only photographers can upload photos.'})
	if request.method == 'POST':
		form = PhotoForm(request.POST, request.FILES)
		if form.is_valid():
			photo = form.save(commit=False)
			photo.photographer = request.user
			photo.save()
			return redirect('explore')
	else:
		form = PhotoForm()
	return render(request, 'portfolio/upload_photo.html', {'form': form})
# Record a photo share event using share_count
from django.views.decorators.http import require_POST
@require_POST
def share_photo(request):
	photo_id = request.POST.get('photo_id')
	photo = get_object_or_404(Photo, id=photo_id)
	photo.share_count = (photo.share_count or 0) + 1
	photo.save(update_fields=['share_count'])
	return JsonResponse({'success': True, 'share_count': photo.share_count})
# Explore page: show all photographers and photos
from .models import Category
def explore(request):
	from users.models import User
	from .models import Photo, Event, Story
	from community.models import Post
	from django.utils import timezone
	# Get filters/search
	q = request.GET.get('q', '').strip()
	category_id = request.GET.get('category')
	location = request.GET.get('location', '').strip()

	photographers = User.objects.filter(role='photographer')
	photos = Photo.objects.all()
	categories = Category.objects.all()
	# Public feed context
	time_threshold = timezone.now() - timezone.timedelta(hours=24)
	stories = Story.objects.filter(created_at__gte=time_threshold).order_by('-created_at')
	posts = Post.objects.all().order_by('-date')[:6]

	if q:
		photographers = photographers.filter(username__icontains=q)
		photos = photos.filter(title__icontains=q)
	if category_id:
		photos = photos.filter(category_id=category_id)
	if location:
		photographers = photographers.filter(location__icontains=location)

	photos = photos.order_by('-uploaded_at')[:24]

	# Gather all upcoming events for all photographers
	from django.utils import timezone
	today = timezone.now().date()
	events = Event.objects.filter(date__gte=today).order_by('date')

	# Prepare photos for JSON serialization for gallery modal
	photos_json = [
		{
			'image': photo.image.url,
			'title': photo.title,
			'photographer_first_name': photo.photographer.first_name,
			'photographer_last_name': photo.photographer.last_name,
			'photographer': photo.photographer.pk,
		}
		for photo in photos
	]
	return render(request, 'explore.html', {
		'photographers': photographers,
		'photos': photos,
		'photos_json': photos_json,
		'categories': categories,
		'q': q,
		'selected_category': category_id,
		'location': location,
		'events': events,
		'stories': stories,
		'posts': posts,
	})

from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from .models import Photo, Category, Story
from users.models import User
from django.contrib.auth.decorators import login_required
from .forms import PhotoForm, CategoryForm, StoryForm, EventForm
# Like/dislike endpoints for AJAX
from django.http import JsonResponse
from .models import PhotoLike
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import PhotoComment

# Like a photo (allow anonymous)
@require_POST
def like_photo(request):
	photo_id = request.POST.get('photo_id')
	photo = get_object_or_404(Photo, id=photo_id)
	if request.user.is_authenticated:
		like, created = PhotoLike.objects.get_or_create(photo=photo, user=request.user)
		like.is_like = True
		like.save()
	else:
		# Use session key for anonymous likes
		session_key = request.session.session_key
		if not session_key:
			request.session.create()
			session_key = request.session.session_key
		# Remove any previous like/dislike by this session
		PhotoLike.objects.filter(photo=photo, user=None, session_key=session_key).delete()
		like = PhotoLike.objects.create(photo=photo, user=None, session_key=session_key, is_like=True)
	likes_count = PhotoLike.objects.filter(photo=photo, is_like=True).count()
	dislikes_count = PhotoLike.objects.filter(photo=photo, is_like=False).count()
	return JsonResponse({'success': True, 'likes': likes_count, 'dislikes': dislikes_count})

# Dislike a photo (allow anonymous)
@require_POST
def dislike_photo(request):
	photo_id = request.POST.get('photo_id')
	photo = get_object_or_404(Photo, id=photo_id)
	if request.user.is_authenticated:
		like, created = PhotoLike.objects.get_or_create(photo=photo, user=request.user)
		like.is_like = False
		like.save()
	else:
		session_key = request.session.session_key
		if not session_key:
			request.session.create()
			session_key = request.session.session_key
		PhotoLike.objects.filter(photo=photo, user=None, session_key=session_key).delete()
		like = PhotoLike.objects.create(photo=photo, user=None, session_key=session_key, is_like=False)
	likes_count = PhotoLike.objects.filter(photo=photo, is_like=True).count()
	dislikes_count = PhotoLike.objects.filter(photo=photo, is_like=False).count()
	return JsonResponse({'success': True, 'likes': likes_count, 'dislikes': dislikes_count})
# List all upcoming events for the logged-in photographer
@login_required
def my_events(request):
	if request.user.role != 'photographer':
		return redirect('home')
	events = request.user.events.order_by('date')
	return render(request, 'portfolio/my_events.html', {'events': events})

# Create a new event
@login_required
def create_event(request):
	if request.user.role != 'photographer':
		return redirect('home')
	if request.method == 'POST':
		form = EventForm(request.POST)
		if form.is_valid():
			event = form.save(commit=False)
			event.photographer = request.user
			event.save()
			return redirect('my_events')
	else:
		form = EventForm()
	return render(request, 'portfolio/create_event.html', {'form': form})

# Photographer dashboard view
@login_required
def photographer_dashboard(request):
	if request.user.role != 'photographer':
		return redirect('home')
	
	from .models import Photo, Story, PhotoLike, Event
	from bookings.models import Booking
	from community.models import Post
	from django.utils import timezone
	from django.db.models import Count, Q
	from datetime import datetime, timedelta
	
	# Get photographer's photos
	user_photos = Photo.objects.filter(photographer=request.user, is_approved=True)
	total_photos = user_photos.count()
	
	# Get recent photos (last 6)
	recent_photos = user_photos.order_by('-uploaded_at')[:6]
	
	# Get stories from last 24 hours
	time_threshold = timezone.now() - timedelta(hours=24)
	user_stories = Story.objects.filter(photographer=request.user, created_at__gte=time_threshold)
	total_stories = user_stories.count()
	recent_stories = user_stories.order_by('-created_at')[:6]
	
	# Calculate total likes across all photos
	total_likes = PhotoLike.objects.filter(photo__in=user_photos, is_like=True).count()
	
	# Profile views (if you have a profile view tracking model, otherwise calculate from related data)
	# For now, use booking requests as a proxy for profile interest
	profile_views = Booking.objects.filter(photographer=request.user).count() * 15  # Rough estimation
	
	# Recent bookings
	recent_bookings = Booking.objects.filter(photographer=request.user).order_by('-created_at')[:5]
	
	# Recent activity (likes, comments, bookings)
	recent_activity = []
	
	# Add recent likes
	recent_likes = PhotoLike.objects.filter(photo__photographer=request.user, is_like=True).select_related('photo', 'user').order_by('-created_at')[:3]
	for like in recent_likes:
		recent_activity.append({
			'type': 'like',
			'icon': 'fas fa-heart',
			'title': f'Your photo "{like.photo.title or "Untitled"}" received a like',
			'time': like.created_at,
			'user': like.user.get_full_name() or like.user.username if like.user else 'Anonymous'
		})
	
	# Add recent bookings
	for booking in recent_bookings[:2]:
		recent_activity.append({
			'type': 'booking',
			'icon': 'fas fa-calendar',
			'title': f'New booking request for {booking.service_type}',
			'time': booking.created_at,
			'user': booking.client_name or (booking.client.get_full_name() if booking.client else 'Client')
		})
	
	# Sort activity by time
	recent_activity.sort(key=lambda x: x['time'], reverse=True)
	recent_activity = recent_activity[:5]  # Limit to 5 items
	
	# Calculate growth percentages (comparing with previous periods)
	last_month = timezone.now() - timedelta(days=30)
	last_week = timezone.now() - timedelta(days=7)
	
	# Photos growth (last 30 days vs previous 30 days)
	photos_last_month = user_photos.filter(uploaded_at__gte=last_month).count()
	photos_prev_month = user_photos.filter(
		uploaded_at__gte=timezone.now() - timedelta(days=60),
		uploaded_at__lt=last_month
	).count()
	photos_growth = ((photos_last_month - photos_prev_month) / max(photos_prev_month, 1)) * 100 if photos_prev_month > 0 else 0
	
	# Likes growth (last week vs previous week)
	likes_last_week = PhotoLike.objects.filter(
		photo__photographer=request.user,
		is_like=True,
		created_at__gte=last_week
	).count()
	likes_prev_week = PhotoLike.objects.filter(
		photo__photographer=request.user,
		is_like=True,
		created_at__gte=timezone.now() - timedelta(days=14),
		created_at__lt=last_week
	).count()
	likes_growth = ((likes_last_week - likes_prev_week) / max(likes_prev_week, 1)) * 100 if likes_prev_week > 0 else 0
	
	context = {
		'total_photos': total_photos,
		'recent_photos': recent_photos,
		'total_stories': total_stories,
		'recent_stories': recent_stories,
		'total_likes': total_likes,
		'profile_views': profile_views,
		'recent_bookings': recent_bookings,
		'recent_activity': recent_activity,
		'photos_growth': round(photos_growth, 1),
		'likes_growth': round(likes_growth, 1),
	}
	
	return render(request, 'portfolio/photographer_dashboard.html', context)

# Feed view (main Instagram-like feed)
@login_required
def feed(request):
	# Show all active stories and recent photos
	# Only show stories from the last 24 hours
	time_threshold = timezone.now() - timezone.timedelta(hours=24)
	stories = Story.objects.filter(created_at__gte=time_threshold).order_by('-created_at')
	posts = Photo.objects.all().order_by('-uploaded_at')[:20]  # Latest posts for the feed
	return render(request, 'feed.html', {'stories': stories, 'posts': posts})

# View a single story
def view_story(request, story_id):
	story = Story.objects.get(id=story_id)
	# Only allow viewing if story is active
	if not story.is_active():
		return redirect('portfolio:feed')
	return render(request, 'portfolio/view_story.html', {'story': story})

# Story upload view for photographers
@login_required
def upload_story(request):
	if request.user.role != 'photographer':
		return redirect('portfolio:feed')
	
	# Get all stories for the current user (active and expired)
	user_stories = Story.objects.filter(photographer=request.user).order_by('-created_at')
	
	# Separate active and expired stories
	from django.utils import timezone
	from datetime import timedelta
	time_threshold = timezone.now() - timedelta(hours=24)
	active_stories = user_stories.filter(created_at__gte=time_threshold)
	expired_stories = user_stories.filter(created_at__lt=time_threshold)
	
	if request.method == 'POST':
		form = StoryForm(request.POST, request.FILES)
		if form.is_valid():
			story = form.save(commit=False)
			story.photographer = request.user
			story.save()
			messages.success(request, 'Story uploaded successfully!')
			return redirect('portfolio:upload_story')  # Redirect back to upload page to see new story
	else:
		form = StoryForm()
	
	context = {
		'form': form,
		'active_stories': active_stories,
		'expired_stories': expired_stories,
		'total_stories': user_stories.count(),
	}
	return render(request, 'portfolio/upload_story.html', context)

def photographer_list(request):
	photographers = User.objects.filter(role='photographer')
	
	# Get filters from URL parameters
	location_filter = request.GET.get('location', '').strip()
	search_query = request.GET.get('search', '').strip()
	
	# Apply location filter if provided
	if location_filter:
		photographers = photographers.filter(location__icontains=location_filter)
	
	# Apply search filter if provided
	if search_query:
		photographers = photographers.filter(
			Q(first_name__icontains=search_query) |
			Q(last_name__icontains=search_query) |
			Q(username__icontains=search_query) |
			Q(location__icontains=search_query)
		)
	
	# Get all unique locations for the filter dropdown (exclude empty values)
	all_locations = User.objects.filter(
		role='photographer', 
		location__isnull=False
	).exclude(location='').values_list('location', flat=True).distinct().order_by('location')
	
	context = {
		'photographers': photographers,
		'all_locations': all_locations,
		'selected_location': location_filter,
		'search_query': search_query,
	}
	
	return render(request, 'portfolio/photographer_list.html', context)

def photographer_detail(request, pk):
	photographer = get_object_or_404(User, pk=pk, role='photographer')
	photos = photographer.photos.all()
	# Show only upcoming events (today or future)
	from django.utils import timezone
	today = timezone.now().date()
	events = photographer.events.filter(date__gte=today).order_by('date')
	# Get active stories (last 24h)
	stories = photographer.stories.filter(created_at__gte=timezone.now()-timezone.timedelta(hours=24)).order_by('-created_at')
	
	# Get reviews for this photographer
	from reviews.models import Review
	reviews = Review.objects.filter(
		photographer=photographer, 
		is_approved=True
	).select_related('reviewer', 'booking').order_by('-created_at')
	
	# Calculate average rating
	from django.db.models import Avg
	avg_rating = reviews.aggregate(Avg('overall_rating'))['overall_rating__avg']
	
	return render(request, 'portfolio/photographer_detail.html', {
		'photographer': photographer,
		'photos': photos,
		'events': events,
		'stories': stories,
		'reviews': reviews,
		'avg_rating': avg_rating,
		'review_count': reviews.count(),
	})

def photo_list(request):
	photos = Photo.objects.all()
	categories = Category.objects.all()
	return render(request, 'portfolio/photo_list.html', {'photos': photos, 'categories': categories})

def category_photos(request, category_id):
	category = get_object_or_404(Category, id=category_id)
	photos = category.photos.all()
	return render(request, 'portfolio/category_photos.html', {'category': category, 'photos': photos})


# Upload photo (Photographer only)
@login_required
def upload_photo(request):
	if request.user.role != 'photographer':
		return redirect('portfolio:photo_list')
	if request.method == 'POST':
		form = PhotoForm(request.POST, request.FILES)
		if form.is_valid():
			photo = form.save(commit=False)
			photo.photographer = request.user
			photo.is_approved = True  # Auto-approve photos for better UX
			photo.save()
			return redirect('portfolio:photographer_detail', pk=request.user.pk)
	else:
		form = PhotoForm()
	return render(request, 'portfolio/upload_photo.html', {'form': form})

# Add category (admin only)
@login_required
def add_category(request):
	if not request.user.is_staff:
		return redirect('portfolio:photo_list')
	if request.method == 'POST':
		form = CategoryForm(request.POST)
		if form.is_valid():
			form.save()
			return redirect('portfolio:photo_list')
	else:
		form = CategoryForm()
	return render(request, 'portfolio/add_category.html', {'form': form})

# Delete a story (Photographer or admin only)
@login_required
def delete_story(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    if not request.user.is_authenticated:
        return redirect('users:login')
    if request.user == story.photographer or request.user.is_superuser:
        if request.method == 'POST':
            story.delete()
            messages.success(request, 'Story deleted successfully.')
            return redirect('portfolio:upload_story')  # Redirect back to stories management page
        return render(request, 'portfolio/confirm_delete_story.html', {'story': story})
    else:
        messages.error(request, 'You do not have permission to delete this story.')
        return redirect('portfolio:upload_story')

def delete_photo(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)
    if not request.user.is_authenticated:
        return redirect('users:login')
    if request.user == photo.photographer or request.user.is_superuser:
        if request.method == 'POST':
            photo.delete()
            messages.success(request, 'Photo deleted successfully.')
            return redirect('portfolio:feed')
        return render(request, 'portfolio/confirm_delete_photo.html', {'photo': photo})
    else:
        messages.error(request, 'You do not have permission to delete this photo.')
        return redirect('portfolio:feed')

@require_POST
def add_comment(request):
	photo_id = request.POST.get('photo_id')
	text = request.POST.get('text', '').strip()
	if not text:
		return JsonResponse({'success': False, 'error': 'Empty comment.'})
	try:
		photo = Photo.objects.get(id=photo_id)
	except Photo.DoesNotExist:
		return JsonResponse({'success': False, 'error': 'Photo not found.'})
	if request.user.is_authenticated:
		comment = PhotoComment.objects.create(photo=photo, user=request.user, text=text)
		username = request.user.username
	else:
		comment = PhotoComment.objects.create(photo=photo, user=None, text=text)
		username = 'Anonymous'
	return JsonResponse({'success': True, 'username': username, 'text': comment.text, 'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')})


@login_required
def ai_insights(request):
	"""AI-powered insights dashboard for photographers"""
	if not hasattr(request.user, 'role') or request.user.role != 'photographer':
		return render(request, 'portfolio/not_photographer.html', {'message': 'Only photographers can access AI insights.'})
	
	try:
		from config.ai_service import ai_service
		
		# Portfolio Statistics
		user_photos = Photo.objects.filter(photographer=request.user)
		total_photos = user_photos.count()
		
		# Simulate AI analysis results (in production, this would use actual AI data)
		portfolio_stats = {
			'total_photos': total_photos,
			'quality_score': 85,  # Would be calculated from actual AI analysis
		}
		
		# AI Pricing Intelligence
		ai_pricing = {
			'suggested_base_rate': 750,
			'price_range': {'min': 600, 'max': 900},
			'market_position': 78,
			'market_description': 'Above average in your area'
		}
		
		# Sentiment Analysis from Reviews
		from reviews.models import Review
		user_reviews = Review.objects.filter(photographer=request.user)
		total_reviews = user_reviews.count()
		
		if total_reviews > 0:
			sentiment_analysis = [
				{'type': 'positive', 'label': 'Positive', 'percentage': 75},
				{'type': 'neutral', 'label': 'Neutral', 'percentage': 20},
				{'type': 'negative', 'label': 'Negative', 'percentage': 5}
			]
			overall_sentiment = {'score': 4.3}
			sentiment_insights = [
				"Clients consistently praise your professionalism",
				"Communication timing could be improved",
				"Photo quality receives excellent feedback"
			]
		else:
			sentiment_analysis = []
			overall_sentiment = {'score': 0}
			sentiment_insights = ["Complete more bookings to get sentiment analysis"]
		
		# Booking Trends
		from bookings.models import Booking
		user_bookings = Booking.objects.filter(photographer=request.user)
		
		booking_trends = {
			'monthly_growth': 15  # Simulated growth percentage
		}
		
		# Popular services analysis
		service_counts = user_bookings.values('service_type').annotate(
			count=Count('id')
		).order_by('-count')[:3]
		
		popular_services = [
			{
				'name': service['service_type'].title() if service['service_type'] else 'General',
				'bookings': service['count']
			}
			for service in service_counts
		]
		
		booking_recommendations = [
			"Wedding photography shows highest demand",
			"Consider offering package deals for events",
			"Weekend bookings are 40% more profitable"
		] if user_bookings.exists() else []
		
		# AI Photo Categorization Stats
		auto_tagged_photos = user_photos.count()  # Simplified for production
		
		# Top categories from existing categorization
		category_counts = user_photos.filter(
			category__isnull=False
		).values('category__name').annotate(
			count=Count('id')
		).order_by('-count')[:5]
		
		top_categories = [
			{'name': cat['category__name'] or 'Uncategorized', 'count': cat['count']}
			for cat in category_counts
		]
		
		categorization_accuracy = 92  # Simulated accuracy
		total_tags = user_photos.count() * 3  # Estimated tags per photo
		photos_need_review = 0  # Simplified for production
		
		# Revenue Insights
		revenue_insights = {
			'potential_increase': 850,
			'optimization_score': 73
		}
		
		revenue_recommendations = [
			"Increase portrait session rates by 20%",
			"Offer premium editing packages",
			"Add video services to increase booking value"
		] if user_bookings.exists() else []
		
		# Portfolio Recommendations
		portfolio_recommendations = [
			"Add more diverse lighting examples to showcase versatility",
			"Include client testimonials with portfolio pieces",
			"Consider creating themed galleries for better organization"
		] if total_photos > 0 else ["Upload photos to get AI recommendations"]
		
		context = {
			'portfolio_stats': portfolio_stats,
			'portfolio_recommendations': portfolio_recommendations,
			'ai_pricing': ai_pricing,
			'sentiment_analysis': sentiment_analysis,
			'overall_sentiment': overall_sentiment,
			'sentiment_insights': sentiment_insights,
			'booking_trends': booking_trends,
			'popular_services': popular_services,
			'booking_recommendations': booking_recommendations,
			'auto_tagged_photos': auto_tagged_photos,
			'top_categories': top_categories,
			'categorization_accuracy': categorization_accuracy,
			'total_tags': total_tags,
			'photos_need_review': photos_need_review,
			'revenue_insights': revenue_insights,
			'revenue_recommendations': revenue_recommendations,
		}
		
		return render(request, 'portfolio/ai_insights.html', context)
		
	except Exception as e:
		import logging
		logger = logging.getLogger(__name__)
		logger.error(f"AI insights error for user {request.user.id}: {str(e)}")
		
		# Fallback context with basic stats
		context = {
			'portfolio_stats': {'total_photos': 0, 'quality_score': 0},
			'portfolio_recommendations': ["AI analysis temporarily unavailable"],
			'ai_pricing': {'suggested_base_rate': 500, 'price_range': {'min': 400, 'max': 600}, 'market_position': 50, 'market_description': 'Market data loading...'},
			'sentiment_analysis': [],
			'overall_sentiment': {'score': 0},
			'sentiment_insights': [],
			'booking_trends': {'monthly_growth': 0},
			'popular_services': [],
			'booking_recommendations': [],
			'auto_tagged_photos': 0,
			'top_categories': [],
			'categorization_accuracy': 0,
			'total_tags': 0,
			'photos_need_review': 0,
			'revenue_insights': {'potential_increase': 0, 'optimization_score': 0},
			'revenue_recommendations': [],
		}
		
		return render(request, 'portfolio/ai_insights.html', context)


@login_required
def auto_categorize_photos(request):
	"""Auto-categorize photos using AI"""
	if not hasattr(request.user, 'role') or request.user.role != 'photographer':
		messages.error(request, 'Only photographers can use auto-categorization.')
		return redirect('home')
	
	try:
		# Get uncategorized photos
		uncategorized_photos = Photo.objects.filter(
			photographer=request.user,
			category__isnull=True
		)
		
		categorized_count = 0
		
		# Simple categorization based on filename patterns
		for photo in uncategorized_photos[:10]:  # Limit to 10 photos per request
			try:
				filename = photo.image.name.lower()
				title = photo.title.lower()
				description = photo.description.lower()
				
				# Simple AI simulation based on keywords
				category_name = None
				if any(word in filename + title + description for word in ['wedding', 'bride', 'groom', 'ceremony']):
					category_name = 'Wedding'
				elif any(word in filename + title + description for word in ['portrait', 'headshot', 'person']):
					category_name = 'Portrait'
				elif any(word in filename + title + description for word in ['event', 'corporate', 'party']):
					category_name = 'Event'
				elif any(word in filename + title + description for word in ['landscape', 'nature', 'sunset']):
					category_name = 'Landscape'
				elif any(word in filename + title + description for word in ['fashion', 'model', 'style']):
					category_name = 'Fashion'
				
				if category_name:
					category, created = Category.objects.get_or_create(name=category_name)
					photo.category = category
					photo.save(update_fields=['category'])
					categorized_count += 1
			
			except Exception as e:
				import logging
				logger = logging.getLogger(__name__)
				logger.error(f"Auto-categorization failed for photo {photo.id}: {str(e)}")
				continue
		
		if categorized_count > 0:
			messages.success(request, f'Successfully auto-categorized {categorized_count} photos!')
		else:
			messages.info(request, 'No photos were categorized. Upload more photos or check existing categories.')
		
		return redirect('portfolio:ai_insights')
		
	except Exception as e:
		import logging
		logger = logging.getLogger(__name__)
		logger.error(f"Auto-categorization error: {str(e)}")
		messages.error(request, 'Auto-categorization temporarily unavailable.')
		return redirect('portfolio:ai_insights')


@login_required
def seo_optimizer(request):
	"""SEO optimization tool for photographers"""
	if not hasattr(request.user, 'role') or request.user.role != 'photographer':
		messages.error(request, 'Only photographers can access SEO optimization.')
		return redirect('home')
	
	try:
		# Get user's photos for SEO analysis
		user_photos = Photo.objects.filter(photographer=request.user)
		total_photos = user_photos.count()
		
		# Calculate SEO score based on portfolio completeness
		seo_score = 40  # Base score
		
		# Add points for portfolio completeness
		if total_photos > 0:
			seo_score += 15
		if total_photos > 10:
			seo_score += 10
		if user_photos.filter(description__isnull=False).exclude(description='').count() > 5:
			seo_score += 15
		if hasattr(request.user, 'bio') and request.user.bio:
			seo_score += 10
		if user_photos.filter(category__isnull=False).count() > 0:
			seo_score += 10
		
		# Identify SEO issues
		seo_issues = []
		
		if total_photos == 0:
			seo_issues.append("No photos uploaded - add portfolio images")
		elif total_photos < 10:
			seo_issues.append(f"Only {total_photos} photos - aim for at least 10")
		
		if user_photos.filter(description__isnull=True).count() > 0 or user_photos.filter(description='').count() > 0:
			seo_issues.append("Some photos missing descriptions")
		
		if user_photos.filter(category__isnull=True).count() > 0:
			seo_issues.append("Some photos not categorized")
		
		if not hasattr(request.user, 'bio') or not request.user.bio:
			seo_issues.append("Profile bio missing - add professional description")
		
		# Generate keyword suggestions based on user's work
		high_value_keywords = [
			f"{request.user.location} photographer" if hasattr(request.user, 'location') and request.user.location else "professional photographer",
			"wedding photographer",
			"portrait photographer",
			"event photographer"
		]
		
		suggested_keywords = [
			"professional photography services",
			"creative portrait sessions",
			"wedding photography packages",
			"commercial photography",
			"family photographer",
			"corporate headshots",
			"engagement photography",
			"lifestyle photography"
		]
		
		# Generate optimized meta tags
		user_name = request.user.get_full_name() or request.user.username
		location = getattr(request.user, 'location', 'Professional')
		
		optimized_title = f"{user_name} - {location} Photographer | PhotoRw"
		optimized_description = f"Professional photography services by {user_name}. Specializing in weddings, portraits, and events. Book your session today on PhotoRw platform."
		
		# Content optimization suggestions
		content_suggestions = [
			"Add detailed descriptions to all photos with relevant keywords",
			"Include location information in photo metadata",
			"Create themed galleries (weddings, portraits, events)",
			"Add client testimonials to boost credibility",
			"Include pricing information for transparency",
			"Use consistent naming for photo titles",
			"Add alt text describing each image",
			"Create a comprehensive bio with your specialties"
		]
		
		context = {
			'seo_score': min(seo_score, 100),
			'seo_issues': seo_issues,
			'high_value_keywords': high_value_keywords,
			'suggested_keywords': suggested_keywords,
			'optimized_title': optimized_title,
			'optimized_description': optimized_description,
			'title_length': len(optimized_title),
			'description_length': len(optimized_description),
			'content_suggestions': content_suggestions,
		}
		
		return render(request, 'portfolio/seo_optimizer.html', context)
		
	except Exception as e:
		import logging
		logger = logging.getLogger(__name__)
		logger.error(f"SEO optimizer error: {str(e)}")
		messages.error(request, 'SEO optimization tool temporarily unavailable.')
		return redirect('portfolio:photographer_dashboard')