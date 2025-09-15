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
	return render(request, 'portfolio/photographer_dashboard.html')

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
		return redirect('feed')
	return render(request, 'portfolio/view_story.html', {'story': story})

# Story upload view for photographers
@login_required
def upload_story(request):
	if request.user.role != 'photographer':
		return redirect('feed')
	if request.method == 'POST':
		form = StoryForm(request.POST, request.FILES)
		if form.is_valid():
			story = form.save(commit=False)
			story.photographer = request.user
			story.save()
			return redirect('feed')
	else:
		form = StoryForm()
	return render(request, 'portfolio/upload_story.html', {'form': form})

def photographer_list(request):
	photographers = User.objects.filter(role='photographer')
	return render(request, 'portfolio/photographer_list.html', {'photographers': photographers})

def photographer_detail(request, pk):
	photographer = get_object_or_404(User, pk=pk, role='photographer')
	photos = photographer.photos.all()
	# Show only upcoming events (today or future)
	from django.utils import timezone
	today = timezone.now().date()
	events = photographer.events.filter(date__gte=today).order_by('date')
	# Get active stories (last 24h)
	stories = photographer.stories.filter(created_at__gte=timezone.now()-timezone.timedelta(hours=24)).order_by('-created_at')
	return render(request, 'portfolio/photographer_detail.html', {
		'photographer': photographer,
		'photos': photos,
		'events': events,
		'stories': stories,
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
		return redirect('photo_list')
	if request.method == 'POST':
		form = PhotoForm(request.POST, request.FILES)
		if form.is_valid():
			photo = form.save(commit=False)
			photo.photographer = request.user
			photo.save()
			return redirect('photographer_detail', pk=request.user.pk)
	else:
		form = PhotoForm()
	return render(request, 'portfolio/upload_photo.html', {'form': form})

# Add category (admin only)
@login_required
def add_category(request):
	if not request.user.is_staff:
		return redirect('photo_list')
	if request.method == 'POST':
		form = CategoryForm(request.POST)
		if form.is_valid():
			form.save()
			return redirect('photo_list')
	else:
		form = CategoryForm()
	return render(request, 'portfolio/add_category.html', {'form': form})

# Delete a story (Photographer or admin only)
@login_required
def delete_story(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user == story.photographer or request.user.is_superuser:
        if request.method == 'POST':
            story.delete()
            messages.success(request, 'Story deleted successfully.')
            return redirect('feed')
        return render(request, 'portfolio/confirm_delete_story.html', {'story': story})
    else:
        messages.error(request, 'You do not have permission to delete this story.')
        return redirect('feed')

def delete_photo(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user == photo.photographer or request.user.is_superuser:
        if request.method == 'POST':
            photo.delete()
            messages.success(request, 'Photo deleted successfully.')
            return redirect('feed')
        return render(request, 'portfolio/confirm_delete_photo.html', {'photo': photo})
    else:
        messages.error(request, 'You do not have permission to delete this photo.')
        return redirect('feed')

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
