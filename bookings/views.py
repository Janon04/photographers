# Email and URL imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Booking
from users.models import User
from django import forms
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings
# Utility: send booking notification email
def send_booking_email(subject, message, recipient):
    if recipient and recipient.strip():
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            fail_silently=True,
        )
# Client cancels their booking
@login_required
@require_POST
def cancel_booking(request, booking_id):
	booking = get_object_or_404(Booking, id=booking_id)
	if request.user == booking.client or request.user == booking.photographer:
		if booking.status in ['pending', 'confirmed']:
			booking.status = 'cancelled'
			booking.save()
			# Email notification to both parties
			subject = 'Booking Cancelled'
			client_name = f"{booking.client.first_name} {booking.client.last_name}".strip() or booking.client.email
			photographer_name = f"{booking.photographer.first_name} {booking.photographer.last_name}".strip() or booking.photographer.email
			message = f"Booking between {client_name} and {photographer_name} on {booking.date} at {booking.time} has been cancelled."
			send_booking_email(subject, message, booking.client.email)
			send_booking_email(subject, message, booking.photographer.email)
			messages.success(request, 'Booking cancelled.')
	return redirect(request.META.get('HTTP_REFERER', reverse('client_dashboard')))

# Photographer confirms a booking
@login_required
@require_POST
def confirm_booking(request, booking_id):
	booking = get_object_or_404(Booking, id=booking_id, photographer=request.user)
	if booking.status == 'pending':
		booking.status = 'confirmed'
		booking.save()
		# Email notification to client
		subject = 'Your Booking Has Been Confirmed'
		photographer_name = f"{booking.photographer.first_name} {booking.photographer.last_name}".strip() or booking.photographer.email
		message = f"Your booking with {photographer_name} on {booking.date} at {booking.time} has been confirmed."
		if booking.client.email:
			send_booking_email(subject, message, booking.client.email)
		else:
			messages.warning(request, 'Booking confirmed, but client email is missing. No email sent.')
		messages.success(request, 'Booking confirmed!')
	else:
		messages.info(request, 'Booking was not pending.')
	return redirect(request.META.get('HTTP_REFERER', reverse('photographer_dashboard')))

# Photographer marks booking as complete
@login_required
@require_POST
def complete_booking(request, booking_id):
	booking = get_object_or_404(Booking, id=booking_id, photographer=request.user)
	if booking.status == 'confirmed':
		booking.status = 'completed'
		booking.save()
		# Email notification to client
		subject = 'Your Booking is Completed'
		photographer_name = f"{booking.photographer.first_name} {booking.photographer.last_name}".strip() or booking.photographer.email
		message = f"Your booking with {photographer_name} on {booking.date} at {booking.time} is now marked as completed."
		if booking.client.email:
			send_booking_email(subject, message, booking.client.email)
		else:
			messages.warning(request, 'Booking completed, but client email is missing. No email sent.')
		messages.success(request, 'Booking marked as completed!')
	else:
		messages.info(request, 'Booking was not confirmed.')
	return redirect(request.META.get('HTTP_REFERER', reverse('photographer_dashboard')))

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Booking
from users.models import User
from django import forms
from django.contrib import messages

class BookingForm(forms.ModelForm):
    email = forms.EmailField(required=False, help_text='Enter your email so the photographer can contact you.')
    class Meta:
        model = Booking
        fields = ['photographer', 'service_type', 'date', 'time', 'location']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

@login_required
def create_booking(request):
    initial = {}
    photographer_id = request.GET.get('photographer')
    if photographer_id:
        try:
            initial['photographer'] = User.objects.get(pk=photographer_id, role='photographer')
        except User.DoesNotExist:
            pass
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.client = request.user
            # Use form email if user has no email
            client_email = request.user.email or form.cleaned_data.get('email')
            if not client_email:
                messages.error(request, 'You must provide an email address to make a booking.')
                return render(request, 'bookings/create_booking.html', {'form': form})
            # Require photographer email
            if not booking.photographer.email:
                messages.error(request, 'This photographer does not have an email address set. Please choose another photographer or contact support.')
                return redirect('client_dashboard')
            booking.save()
            # Email notification to photographer
            subject = 'New Booking Request on PhotoRw'
            client_name = f"{request.user.first_name} {request.user.last_name}".strip() or client_email
            message = f"You have a new booking request from {client_name} for {booking.date} at {booking.time}. Contact: {client_email}"
            if booking.photographer.email and booking.photographer.email.strip():
                send_booking_email(subject, message, booking.photographer.email)
                messages.success(request, 'Booking request sent!')
            else:
                messages.error(request, 'Booking created, but photographer has no valid email. Please contact them directly.')
            return redirect('client_dashboard')
    else:
        form = BookingForm(initial=initial)
    return render(request, 'bookings/create_booking.html', {'form': form})

@login_required
def client_dashboard(request):
	bookings = Booking.objects.filter(client=request.user)
	return render(request, 'bookings/client_dashboard.html', {'bookings': bookings})

@login_required
def photographer_dashboard(request):
	bookings = Booking.objects.filter(photographer=request.user)
	return render(request, 'bookings/photographer_dashboard.html', {'bookings': bookings})
