# Email and URL imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Booking
from users.models import User
from django import forms
from .forms import BookingForm
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings
# Utility: send booking notification email
def send_booking_email(subject, message, recipient, html_message=None):
    if recipient and recipient.strip():
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            fail_silently=True,
            html_message=html_message,
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
            client_name = f"{booking.client.first_name} {booking.client.last_name}".strip() if booking.client else (booking.client_name or booking.client_email or 'Anonymous')
            photographer_name = f"{booking.photographer.first_name} {booking.photographer.last_name}".strip() or booking.photographer.email
            message = f"Hello,\n\nThe booking between {client_name} and {photographer_name} on {booking.date} at {booking.time} has been cancelled.\n\nService: {booking.service_type}\nLocation: {booking.location}\n\nIf you have questions, please contact support.\n\nThank you,\nPhotoRw Team"
            html_message = f"""
                <h2>Booking Cancelled</h2>
                <p><strong>Client:</strong> {client_name}<br>
                <strong>Photographer:</strong> {photographer_name}<br>
                <strong>Service:</strong> {booking.service_type}<br>
                <strong>Date:</strong> {booking.date} at {booking.time}<br>
                <strong>Location:</strong> {booking.location}</p>
                <p>This booking has been cancelled. If you have questions, please contact support.</p>
                <br><p>Thank you,<br>PhotoRw Team</p>
            """
            send_booking_email(subject, message, booking.client.email, html_message=html_message)
            send_booking_email(subject, message, booking.photographer.email, html_message=html_message)
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
        client_name = f"{booking.client.first_name} {booking.client.last_name}".strip() or booking.client.email
        message = f"Hello {client_name},\n\nYour booking with {photographer_name} on {booking.date} at {booking.time} has been confirmed!\n\nService: {booking.service_type}\nLocation: {booking.location}\n\nYou can view your booking details in your dashboard.\n\nThank you,\nPhotoRw Team"
        html_message = f"""
            <h2>Booking Confirmed</h2>
            <p><strong>Photographer:</strong> {photographer_name}<br>
            <strong>Service:</strong> {booking.service_type}<br>
            <strong>Date:</strong> {booking.date} at {booking.time}<br>
            <strong>Location:</strong> {booking.location}</p>
            <p>Your booking has been confirmed! You can view details in your <a href='http://127.0.0.1:8000/bookings/client/'>dashboard</a>.</p>
            <br><p>Thank you,<br>PhotoRw Team</p>
        """
        if booking.client and booking.client.email:
            send_booking_email(subject, message, booking.client.email, html_message=html_message)
        elif booking.client_name and booking.client_email:
            send_booking_email(subject, message, booking.client_email, html_message=html_message)
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
        if booking.client and booking.client.email:
            send_booking_email(subject, message, booking.client.email)
        elif booking.client_name and booking.client_email:
            send_booking_email(subject, message, booking.client_email)
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


def create_booking(request):
    initial = {}
    photographer_id = request.GET.get('photographer')
    if photographer_id:
        try:
            initial['photographer'] = User.objects.get(pk=photographer_id, role='photographer')
        except User.DoesNotExist:
            pass
    if request.method == 'POST':
        form = BookingForm(request.POST, user=request.user if request.user.is_authenticated else None)
        if form.is_valid():
            booking = form.save(commit=False)
            if request.user.is_authenticated:
                booking.client = request.user
                client_email = request.user.email or form.cleaned_data.get('client_email')
                client_name = f"{request.user.first_name} {request.user.last_name}".strip() or client_email
                booking.client_name = client_name
                booking.client_email = client_email
                booking.client_phone = request.user.profile.phone if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'phone') else ''
            else:
                booking.client = None
                client_email = form.cleaned_data.get('client_email')
                client_name = form.cleaned_data.get('client_name') or client_email
                booking.client_name = client_name
                booking.client_email = client_email
                booking.client_phone = form.cleaned_data.get('client_phone')
            if not client_email:
                messages.error(request, 'You must provide an email address to make a booking.')
                return render(request, 'bookings/create_booking.html', {'form': form})
            if not booking.photographer.email:
                messages.error(request, 'This photographer does not have an email address set. Please choose another photographer or contact support.')
                return redirect('client_dashboard')
            booking.save()
            # Email notification to photographer
            subject = 'New Booking Request on PhotoRw'
            message = f"Hello {booking.photographer.get_full_name() or booking.photographer.email},\n\nYou have received a new booking request on PhotoRw!\n\nClient: {client_name}\nEmail: {client_email}\nPhone: {booking.client_phone or '-'}\nService: {booking.service_type}\nDate: {booking.date} at {booking.time}\nLocation: {booking.location}\n\nPlease log in to your dashboard to confirm or manage this booking.\n\nThank you,\nPhotoRw Team"
            html_message = f"""
                <h2>New Booking Request</h2>
                <p><strong>Client:</strong> {client_name}<br>
                <strong>Email:</strong> {client_email}<br>
                <strong>Phone:</strong> {booking.client_phone or '-'}<br>
                <strong>Service:</strong> {booking.service_type}<br>
                <strong>Date:</strong> {booking.date} at {booking.time}<br>
                <strong>Location:</strong> {booking.location}</p>
                <p>Please <a href='http://127.0.0.1:8000/bookings/photographer/'>log in</a> to your dashboard to confirm or manage this booking.</p>
                <br><p>Thank you,<br>PhotoRw Team</p>
            """
            if booking.photographer.email and booking.photographer.email.strip():
                send_booking_email(subject, message, booking.photographer.email, html_message=html_message)
            # Show thank you message page for all users
            return render(request, 'bookings/booking_success.html')
    else:
        form = BookingForm(initial=initial, user=request.user if request.user.is_authenticated else None)
    return render(request, 'bookings/create_booking.html', {'form': form})

@login_required
def client_dashboard(request):
	bookings = Booking.objects.filter(client=request.user)
	return render(request, 'bookings/client_dashboard.html', {'bookings': bookings})

@login_required
def photographer_dashboard(request):
	bookings = Booking.objects.filter(photographer=request.user)
	return render(request, 'bookings/photographer_dashboard.html', {'bookings': bookings})
