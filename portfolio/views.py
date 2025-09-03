# Explore page: show all photographers and photos
from .models import Category
def explore(request):
	from users.models import User
	from .models import Photo
	# Get filters/search
	q = request.GET.get('q', '').strip()
	category_id = request.GET.get('category')
	location = request.GET.get('location', '').strip()

	photographers = User.objects.filter(role='photographer')
	photos = Photo.objects.all()
	categories = Category.objects.all()

	if q:
		photographers = photographers.filter(username__icontains=q)
		photos = photos.filter(title__icontains=q)
	if category_id:
		photos = photos.filter(category_id=category_id)
	if location:
		photographers = photographers.filter(location__icontains=location)

	photos = photos.order_by('-uploaded_at')[:24]

	return render(request, 'explore.html', {
		'photographers': photographers,
		'photos': photos,
		'categories': categories,
		'q': q,
		'selected_category': category_id,
		'location': location,
	})

from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from .models import Photo, Category, Story
from users.models import User
from django.contrib.auth.decorators import login_required
from .forms import PhotoForm, CategoryForm, StoryForm

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
	photos = Photo.objects.all().order_by('-uploaded_at')[:20]
	return render(request, 'feed.html', {'stories': stories, 'photos': photos})

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
	return render(request, 'portfolio/photographer_detail.html', {'photographer': photographer, 'photos': photos})

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
