from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Message
from .forms import CustomUserCreationForm, PhotographerSearchForm, MessageForm
from config.email_service import EmailService

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, BadHeaderError
import logging

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.http import JsonResponse
from utils.rwanda_locations import get_districts, get_sectors, get_cells, get_villages
from .forms import ProfileForm

# Get logger for this module
logger = logging.getLogger(__name__)

def register(request):
	if request.method == 'POST':
		form = CustomUserCreationForm(request.POST, request.FILES)
		if form.is_valid():
			user = form.save(commit=False)
			user.is_verified = False
			user.save()
			logger.info(f"New user registered: {user.email}")
			
			# Send professional activation email using EmailService
			email_sent = EmailService.send_activation_email(user, request)
			
			if email_sent:
				messages.success(request, 'Registration successful! Please check your email to activate your account.')
			else:
				messages.warning(request, 'Registration successful! However, we could not send the activation email. Please contact support.')
			
			return redirect('users:login')
		else:
			logger.warning(f"Registration form invalid: {form.errors}")
	else:
		form = CustomUserCreationForm()
	return render(request, 'users/register.html', {'form': form})

def activate(request, uidb64, token):
	try:
		uid = force_str(urlsafe_base64_decode(uidb64))
		user = User.objects.get(pk=uid)
	except (TypeError, ValueError, OverflowError, User.DoesNotExist):
		user = None
	if user and default_token_generator.check_token(user, token):
		user.is_verified = True
		user.save()
		messages.success(request, 'Your account has been activated! You can now log in.')
		return redirect('users:login')
	else:
		messages.error(request, 'Activation link is invalid or expired.')
		return redirect('users:login')

def user_login(request):
	if request.method == 'POST':
		form = AuthenticationForm(request, data=request.POST)
		if form.is_valid():
			user = form.get_user()
			if not user.is_verified:
				messages.error(request, 'Please verify your email before logging in.')
				return render(request, 'users/login.html', {'form': form})
			login(request, user)
			return redirect('/portfolio/feed/')
	else:
		form = AuthenticationForm()
	return render(request, 'users/login.html', {'form': form})

@login_required
def user_logout(request):
	if request.method == 'POST':
		logout(request)
		return redirect('home')
	return render(request, 'users/logout.html')  # Optional: render a logout confirmation page

@login_required
def profile(request, user_id=None):
    if user_id:
        user = get_object_or_404(User, pk=user_id)
        is_own_profile = user == request.user
    else:
        user = request.user
        is_own_profile = True
    
    # Handle email update for own profile
    if request.method == 'POST' and 'email' in request.POST and is_own_profile:
        new_email = request.POST.get('email', '').strip()
        if new_email and new_email != request.user.email:
            request.user.email = new_email
            request.user.save()
            messages.success(request, 'Email updated successfully!')
        else:
            messages.info(request, 'No changes made to your email.')
    
    # Get user's blog posts if viewing own profile
    user_blog_posts = None
    if is_own_profile:
        from blog.models import BlogPost
        user_blog_posts = BlogPost.objects.filter(owner=user).order_by('-created_at')[:5]  # Latest 5 posts
    
    context = {
        'user': user,
        'is_own_profile': is_own_profile,
        'user_blog_posts': user_blog_posts,
    }
    
    return render(request, 'users/profile.html', context)


@login_required
def edit_profile(request):
    """Allow a logged-in user to edit their profile."""
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('users:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileForm(instance=user)

    return render(request, 'users/edit_profile.html', {'form': form})

@login_required
def dashboard(request):
    """User dashboard with blog management and overview"""
    from blog.models import BlogPost
    
    # Get user's blog posts
    user_blog_posts = BlogPost.objects.filter(owner=request.user).order_by('-created_at')
    
    # Blog statistics
    total_posts = user_blog_posts.count()
    published_posts = user_blog_posts.filter(is_published=True).count()
    draft_posts = user_blog_posts.filter(is_published=False).count()
    
    # Recent activity
    recent_posts = user_blog_posts[:3]
    
    context = {
        'user_blog_posts': user_blog_posts,
        'total_posts': total_posts,
        'published_posts': published_posts,
        'draft_posts': draft_posts,
        'recent_posts': recent_posts,
    }
    
    return render(request, 'users/dashboard.html', context)

def photographer_search(request):
    form = PhotographerSearchForm(request.GET or None)
    photographers = User.objects.filter(role='photographer')

    if form.is_valid():
        location = form.cleaned_data.get('location')
        province = form.cleaned_data.get('province')
        district = form.cleaned_data.get('district')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        min_rating = form.cleaned_data.get('min_rating')
        role = form.cleaned_data.get('role')

        if location:
            photographers = photographers.filter(location__icontains=location)
        if province:
            photographers = photographers.filter(location__icontains=province)
        if district:
            photographers = photographers.filter(location__icontains=district)
        if min_price is not None:
            photographers = photographers.filter(price__gte=min_price)
        if max_price is not None:
            photographers = photographers.filter(price__lte=max_price)
        if min_rating is not None:
            photographers = photographers.filter(average_rating__gte=min_rating)
        if role:
            photographers = photographers.filter(role=role)

    return render(request, 'users/photographer_search.html', {
        'form': form,
        'photographers': photographers
    })

@login_required
def inbox(request):
    messages = Message.objects.filter(receiver=request.user).order_by('-timestamp')
    return render(request, 'users/inbox.html', {'messages': messages})

@login_required
def send_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            return redirect('inbox')
    else:
        form = MessageForm()
    return render(request, 'users/send_message.html', {'form': form})

# AJAX views for cascading location dropdowns
def get_districts_ajax(request):
    """AJAX view to get districts based on province"""
    province = request.GET.get('province')
    districts = get_districts(province) if province else []
    return JsonResponse({'districts': districts})

def get_sectors_ajax(request):
    """AJAX view to get sectors based on province and district"""
    province = request.GET.get('province')
    district = request.GET.get('district')
    sectors = get_sectors(province, district) if province and district else []
    return JsonResponse({'sectors': sectors})

def get_cells_ajax(request):
    """AJAX view to get cells based on province, district, and sector"""
    province = request.GET.get('province')
    district = request.GET.get('district')
    sector = request.GET.get('sector')
    cells = get_cells(province, district, sector) if province and district and sector else []
    return JsonResponse({'cells': cells})

def get_villages_ajax(request):
    """AJAX view to get villages based on province, district, sector, and cell"""
    province = request.GET.get('province')
    district = request.GET.get('district')
    sector = request.GET.get('sector')
    cell = request.GET.get('cell')
    villages = get_villages(province, district, sector, cell) if province and district and sector and cell else []
    return JsonResponse({'villages': villages})
