
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Review
from users.models import User
from django import forms

class ReviewForm(forms.ModelForm):
	class Meta:
		model = Review
		fields = ['photographer', 'rating', 'comment']

@login_required
def add_review(request):
	if request.method == 'POST':
		form = ReviewForm(request.POST)
		if form.is_valid():
			review = form.save(commit=False)
			review.client = request.user
			review.save()
			return redirect('reviews_list')
	else:
		form = ReviewForm()
	return render(request, 'reviews/add_review.html', {'form': form})

def reviews_list(request):
	reviews = Review.objects.all().select_related('client', 'photographer')
	return render(request, 'reviews/reviews_list.html', {'reviews': reviews})
