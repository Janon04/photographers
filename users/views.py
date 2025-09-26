from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Message
from .forms import CustomUserCreationForm, PhotographerSearchForm, MessageForm

from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator

def register(request):
	if request.method == 'POST':
		form = CustomUserCreationForm(request.POST, request.FILES)
		if form.is_valid():
			user = form.save(commit=False)
			user.is_verified = False
			user.save()
			# Send activation email
			from django.utils.http import urlsafe_base64_encode
			from django.utils.encoding import force_bytes
			from django.template.loader import render_to_string
			from django.core.mail import send_mail
			from django.conf import settings
			from django.contrib.auth.tokens import default_token_generator
			uid = urlsafe_base64_encode(force_bytes(user.pk))
			token = default_token_generator.make_token(user)
			activation_link = request.build_absolute_uri(f"/users/activate/{uid}/{token}/")
			subject = 'Activate your PhotoRw account'
			message = render_to_string('users/activation_email.txt', {'activation_link': activation_link, 'user': user})
			html_message = f"""
				<h2>Activate Your PhotoRw Account</h2>
				<p>Hello {user.get_full_name() or user.username},</p>
				<p>Thank you for registering on PhotoRw! Please click the link below to activate your account:</p>
				<p><a href='{activation_link}'>{activation_link}</a></p>
				<br><p>Welcome to the community,<br>PhotoRw Team</p>
			"""
			send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True, html_message=html_message)
			messages.info(request, 'Please check your email to activate your account.')
			return redirect('login')
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
		return redirect('login')
	else:
		messages.error(request, 'Activation link is invalid or expired.')
		return redirect('login')

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
    else:
        user = request.user
    if request.method == 'POST' and 'email' in request.POST and user == request.user:
        new_email = request.POST.get('email', '').strip()
        if new_email and new_email != request.user.email:
            request.user.email = new_email
            request.user.save()
            messages.success(request, 'Email updated successfully!')
        else:
            messages.info(request, 'No changes made to your email.')
    return render(request, 'users/profile.html', {'user': user})

def photographer_search(request):
    form = PhotographerSearchForm(request.GET or None)
    photographers = User.objects.filter(role='photographer')

    if form.is_valid():
        location = form.cleaned_data.get('location')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        min_rating = form.cleaned_data.get('min_rating')
        role = form.cleaned_data.get('role')

        if location:
            photographers = photographers.filter(location__icontains=location)
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
