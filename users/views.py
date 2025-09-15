
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import CustomUserCreationForm

from django.contrib.auth import logout
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
			send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
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
def profile(request):
	if request.method == 'POST' and 'email' in request.POST:
		new_email = request.POST.get('email', '').strip()
		if new_email and new_email != request.user.email:
			request.user.email = new_email
			request.user.save()
			messages.success(request, 'Email updated successfully!')
		else:
			messages.info(request, 'No changes made to your email.')
	return render(request, 'users/profile.html', {'user': request.user})
