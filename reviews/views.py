
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models
from .models import Review
from users.models import User
from django import forms
from config.email_service import EmailService
import logging

from bookings.models import Booking

logger = logging.getLogger(__name__)

class ReviewForm(forms.ModelForm):
	booking = forms.ModelChoiceField(
		queryset=Booking.objects.none(),
		label='Booking',
		help_text='Select the completed booking you want to review.'
	)
	class Meta:
		model = Review
		fields = ['booking', 'rating', 'comment']


@login_required
def add_review(request):
	# Only allow clients to review their completed bookings that have not been reviewed yet
	completed_bookings = Booking.objects.filter(client=request.user, status='completed').exclude(review__isnull=False)
	if request.method == 'POST':
		form = ReviewForm(request.POST)
		form.fields['booking'].queryset = completed_bookings
		if form.is_valid():
			booking = form.cleaned_data['booking']
			if booking.status != 'completed' or booking.client != request.user:
				form.add_error('booking', 'You can only review your own completed bookings.')
			else:
				review = form.save(commit=False)
				review.reviewer = request.user
				review.photographer = booking.photographer
				review.save()
				
				# Send email notification to photographer
				EmailService.send_review_notification(review)
				
				logger.info(f"New review added by {request.user.email} for photographer {booking.photographer.email}")
				return redirect('reviews_list')
	else:
		form = ReviewForm()
		form.fields['booking'].queryset = completed_bookings
	return render(request, 'reviews/add_review.html', {'form': form})

def reviews_list(request):
	reviews = Review.objects.all().select_related('reviewer', 'photographer')
	return render(request, 'reviews/reviews_list.html', {'reviews': reviews})

@login_required
def sentiment_report(request):
	"""Detailed sentiment analysis report for photographers"""
	if not hasattr(request.user, 'role') or request.user.role != 'photographer':
		return render(request, 'reviews/not_photographer.html', {'message': 'Only photographers can access sentiment reports.'})
	
	# Get reviews for the current photographer
	reviews = Review.objects.filter(photographer=request.user)
	
	# Basic sentiment analysis (in production, this would use actual AI)
	total_reviews = reviews.count()
	
	if total_reviews > 0:
		# Calculate sentiment metrics
		sentiment_data = {
			'total_reviews': total_reviews,
			'average_rating': reviews.aggregate(avg_rating=models.Avg('rating'))['avg_rating'] or 0,
			'sentiment_breakdown': [
				{'sentiment': 'Positive', 'count': reviews.filter(rating__gte=4).count(), 'percentage': 0},
				{'sentiment': 'Neutral', 'count': reviews.filter(rating=3).count(), 'percentage': 0},
				{'sentiment': 'Negative', 'count': reviews.filter(rating__lte=2).count(), 'percentage': 0},
			]
		}
		
		# Calculate percentages
		for item in sentiment_data['sentiment_breakdown']:
			item['percentage'] = round((item['count'] / total_reviews) * 100, 1) if total_reviews > 0 else 0
	else:
		sentiment_data = {
			'total_reviews': 0,
			'average_rating': 0,
			'sentiment_breakdown': []
		}
	
	context = {
		'sentiment_data': sentiment_data,
		'reviews': reviews[:10]  # Show latest 10 reviews
	}
	
	return render(request, 'reviews/sentiment_report.html', context)
