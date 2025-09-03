
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib.auth import logout

class UserRegistrationForm(forms.ModelForm):
	password = forms.CharField(widget=forms.PasswordInput)
	class Meta:
		model = User
		fields = ['first_name', 'last_name', 'email', 'password', 'bio', 'profile_picture', 'location', 'contact_info', 'role']

def register(request):
	if request.method == 'POST':
		form = UserRegistrationForm(request.POST, request.FILES)
		if form.is_valid():
			user = form.save(commit=False)
			user.set_password(form.cleaned_data['password'])
			user.save()
			login(request, user)
			return redirect('profile')
	else:
		form = UserRegistrationForm()
	return render(request, 'users/register.html', {'form': form})

def user_login(request):
	if request.method == 'POST':
		form = AuthenticationForm(request, data=request.POST)
		if form.is_valid():
			user = form.get_user()
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
	return render(request, 'users/profile.html', {'user': request.user})
