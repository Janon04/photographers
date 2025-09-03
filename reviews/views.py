
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Review
from users.models import User
from django import forms


from bookings.models import Booking

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
				return redirect('reviews_list')
	else:
		form = ReviewForm()
		form.fields['booking'].queryset = completed_bookings
	return render(request, 'reviews/add_review.html', {'form': form})

def reviews_list(request):
	reviews = Review.objects.all().select_related('reviewer', 'photographer')
	return render(request, 'reviews/reviews_list.html', {'reviews': reviews})
