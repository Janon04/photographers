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
from config.email_service import EmailService
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging
import json

logger = logging.getLogger(__name__)

# Client cancels their booking
@login_required
@require_POST
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.user == booking.client or request.user == booking.photographer:
        if booking.status in ['pending', 'confirmed']:
            booking.status = 'cancelled'
            booking.save()
            
            # Send professional email notifications to both parties
            EmailService.send_booking_notification(booking, 'cancelled', 'client')
            EmailService.send_booking_notification(booking, 'cancelled', 'photographer')
            
            logger.info(f"Booking {booking_id} cancelled by {request.user.email}")
            messages.success(request, 'Booking cancelled successfully.')
        else:
            messages.error(request, 'This booking cannot be cancelled.')
    else:
        messages.error(request, 'You do not have permission to cancel this booking.')
    
    return redirect(request.META.get('HTTP_REFERER', reverse('bookings:client_dashboard')))

# Photographer confirms a booking
@login_required
@require_POST
def confirm_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, photographer=request.user)
    if booking.status == 'pending':
        booking.status = 'confirmed'
        booking.save()
        
        # Send professional email notification to client
        EmailService.send_booking_notification(booking, 'confirmed', 'client')
        
        logger.info(f"Booking {booking_id} confirmed by photographer {request.user.email}")
        messages.success(request, 'Booking confirmed successfully!')
    else:
        messages.info(request, 'Booking was not pending.')
    
    return redirect(request.META.get('HTTP_REFERER', reverse('bookings:photographer_dashboard')))

# Photographer marks booking as complete
@login_required
@require_POST
def complete_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, photographer=request.user)
    if booking.status == 'confirmed':
        booking.status = 'completed'
        booking.save()
        
        # Send professional email notification to client
        EmailService.send_booking_notification(booking, 'completed', 'client')
        
        logger.info(f"Booking {booking_id} completed by photographer {request.user.email}")
        messages.success(request, 'Booking marked as completed!')
    else:
        messages.info(request, 'Booking was not confirmed.')
    
    return redirect(request.META.get('HTTP_REFERER', reverse('bookings:photographer_dashboard')))

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
                return redirect('bookings:client_dashboard')
            booking.save()
            
            # Send professional email notifications
            EmailService.send_booking_notification(booking, 'pending', 'photographer')
            EmailService.send_booking_notification(booking, 'pending', 'client')
            
            logger.info(f"New booking created: {booking.id} by {client_name}")
            
            # Show thank you message page for all users
            return render(request, 'bookings/booking_success.html', {'booking': booking})
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


@login_required
def pricing_calculator(request):
	"""AI-powered pricing calculator for photographers"""
	if not hasattr(request.user, 'role') or request.user.role != 'photographer':
		messages.error(request, 'Only photographers can access the pricing calculator.')
		return redirect('home')
	
	if request.method == 'POST':
		try:
			# Get form data
			service_type = request.POST.get('service_type')
			duration = int(request.POST.get('duration', 4))
			date = request.POST.get('date')
			location = request.POST.get('location', '')
			experience_level = request.POST.get('experience_level')
			editing_included = request.POST.get('editing_included')
			
			# Base rates for different services (production-ready pricing)
			base_rates = {
				'wedding': 1500,
				'portrait': 350,
				'event': 650,
				'commercial': 900,
				'fashion': 750,
				'landscape': 400,
				'food': 550,
				'sports': 500
			}
			
			# Experience multipliers
			experience_multipliers = {
				'beginner': 0.7,
				'intermediate': 1.0,
				'advanced': 1.3,
				'expert': 1.6
			}
			
			# Editing level multipliers
			editing_multipliers = {
				'none': 0.8,
				'basic': 1.0,
				'standard': 1.2,
				'premium': 1.5
			}
			
			# Duration factor (base is 4 hours)
			duration_multiplier = 1 + (duration - 4) * 0.1
			
			# Location premium for premium areas
			location_multiplier = 1.2 if any(term in location.lower() for term in ['downtown', 'city center', 'luxury', 'resort']) else 1.0
			
			# Calculate final price
			base_price = base_rates.get(service_type, 500)
			experience_mult = experience_multipliers.get(experience_level, 1.0)
			editing_mult = editing_multipliers.get(editing_included, 1.0)
			
			final_price = base_price * experience_mult * editing_mult * duration_multiplier * location_multiplier
			
			# Get photographer's booking count for market position
			booking_count = Booking.objects.filter(photographer=request.user).count()
			market_position = min(90, max(20, 50 + booking_count * 5))
			
			response_data = {
				'success': True,
				'suggested_price': round(final_price, 0),
				'price_range': {
					'min': round(final_price * 0.85, 0),
					'max': round(final_price * 1.15, 0)
				},
				'factors_considered': [
					f"Base {service_type} rate: ${base_price}",
					f"Experience level ({experience_level}): {experience_mult}x",
					f"Editing level ({editing_included}): {editing_mult}x",
					f"Duration ({duration}h): {duration_multiplier:.1f}x",
					f"Location factor: {location_multiplier}x"
				],
				'market_analysis': {
					'position_score': market_position,
					'description': f'{"Above average" if market_position > 60 else "Average" if market_position > 40 else "Growing"} market position'
				},
				'recommendations': [
					"Consider offering package deals for multiple sessions",
					"Add rush delivery fee (20-30%) for quick turnaround",
					"Include travel fees for locations over 30 miles",
					"Offer payment plans for bookings over Rwf 1,000,000"
				]
			}
			
			return JsonResponse(response_data)
			
		except Exception as e:
			logger.error(f"Pricing calculator error: {str(e)}")
			return JsonResponse({
				'success': False,
				'error': 'Pricing calculation failed. Please try again.'
			})
	
	return render(request, 'bookings/pricing_calculator.html')


@login_required
def pricing_calculator(request):
	"""AI-powered pricing calculator for photographers"""
	if not hasattr(request.user, 'role') or request.user.role != 'photographer':
		messages.error(request, 'Only photographers can access the pricing calculator.')
		return redirect('home')
	
	if request.method == 'POST':
		try:
			from config.ai_service import ai_service
			
			# Get form data
			service_type = request.POST.get('service_type')
			duration = int(request.POST.get('duration', 4))
			date = request.POST.get('date')
			location = request.POST.get('location', '')
			experience_level = request.POST.get('experience_level')
			editing_included = request.POST.get('editing_included')
			
			# Prepare photographer profile
			photographer_profile = {
				'years_experience': {
					'beginner': 0.5,
					'intermediate': 2,
					'advanced': 4,
					'expert': 7
				}.get(experience_level, 2),
				'total_bookings': Booking.objects.filter(photographer=request.user).count(),
				'average_rating': 4.2  # Could be calculated from actual reviews
			}
			
			# Prepare booking details
			booking_details = {
				'category': service_type,
				'date': date,
				'location': location,
				'duration': duration,
				'editing_level': editing_included
			}
			
			# Get AI pricing analysis
			pricing_analysis = ai_service.suggest_pricing(
				photographer_profile, 
				booking_details
			)
			
			if 'error' not in pricing_analysis:
				# Apply editing premium
				editing_multiplier = {
					'none': 0.8,
					'basic': 1.0,
					'standard': 1.2,
					'premium': 1.5
				}.get(editing_included, 1.0)
				
				base_price = pricing_analysis['suggested_price']
				final_price = base_price * editing_multiplier
				
				response_data = {
					'success': True,
					'suggested_price': round(final_price, 0),
					'price_range': {
						'min': round(final_price * 0.8, 0),
						'max': round(final_price * 1.2, 0)
					},
					'factors_considered': pricing_analysis['factors_considered'] + [
						f"Editing level ({editing_included}): {editing_multiplier}x"
					],
					'market_analysis': {
						'position_score': min(90, max(10, int((final_price / 1000) * 100))),
						'description': pricing_analysis['market_analysis'].get('category_average', 'Competitive pricing for your market')
					},
					'recommendations': pricing_analysis.get('recommendations', []) + [
						f"Consider {editing_included} editing as your standard offering",
						"Monitor competitor pricing in your area",
						"Adjust rates based on seasonal demand"
					]
				}
			else:
				# Fallback pricing if AI service fails
				base_rates = {
					'wedding': 1200,
					'portrait': 400,
					'event': 600,
					'commercial': 800,
					'fashion': 700,
					'landscape': 300,
					'food': 500,
					'sports': 450
				}
				
				base_price = base_rates.get(service_type, 500)
				experience_multiplier = {
					'beginner': 0.7,
					'intermediate': 1.0,
					'advanced': 1.3,
					'expert': 1.6
				}.get(experience_level, 1.0)
				
				editing_multiplier = {
					'none': 0.8,
					'basic': 1.0,
					'standard': 1.2,
					'premium': 1.5
				}.get(editing_included, 1.0)
				
				final_price = base_price * experience_multiplier * editing_multiplier
				
				response_data = {
					'success': True,
					'suggested_price': round(final_price, 0),
					'price_range': {
						'min': round(final_price * 0.8, 0),
						'max': round(final_price * 1.2, 0)
					},
					'factors_considered': [
						f"Base {service_type} rate: ${base_price}",
						f"Experience level ({experience_level}): {experience_multiplier}x",
						f"Editing level ({editing_included}): {editing_multiplier}x",
						f"Duration ({duration}h): Standard rate"
					],
					'market_analysis': {
						'position_score': 60,
						'description': 'Competitive pricing for your experience level'
					},
					'recommendations': [
						"Price is calculated using industry standards",
						"Consider local market conditions",
						"Adjust based on your portfolio quality",
						"Add travel fees for distant locations"
					]
				}
			
			# Render template with results instead of JSON
			context = {
				'calculation_results': response_data,
				'form_data': {
					'service_type': service_type,
					'duration': duration,
					'experience_level': experience_level,
					'editing_included': editing_included,
					'location': location
				}
			}
			return render(request, 'bookings/pricing_calculator.html', context)
			
		except Exception as e:
			logger.error(f"Pricing calculator error: {str(e)}")
			context = {
				'error_message': 'Pricing calculation failed. Please try again.',
				'calculation_results': None
			}
			return render(request, 'bookings/pricing_calculator.html', context)
	
	return render(request, 'bookings/pricing_calculator.html')
