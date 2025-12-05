
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from decimal import Decimal
from .models import Transaction, SubscriptionPlan, UserSubscription, SubscriptionPayment
from .services import SubscriptionService
from bookings.models import Booking
from users.models import User
from config.email_service import EmailService
import logging
import uuid

logger = logging.getLogger(__name__)

# Subscription Views
def pricing_page(request):
    """Public pricing page showing all subscription plans"""
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price_monthly')
    context = {
        'plans': plans,
        'user_subscription': None
    }
    
    if request.user.is_authenticated:
        try:
            context['user_subscription'] = request.user.subscription
        except UserSubscription.DoesNotExist:
            pass
    
    return render(request, 'payments/pricing.html', context)

@login_required
def subscription_dashboard(request):
    """User's subscription dashboard"""
    subscription = SubscriptionService.get_or_create_user_subscription(request.user)
    
    # Get usage statistics
    usage_stats = {
        'photos_uploaded': subscription.photos_uploaded_this_month,
        'photos_limit': subscription.plan.max_photos_upload,
        'storage_used': float(subscription.storage_used_gb),
        'storage_limit': float(subscription.plan.max_storage_gb) if subscription.plan.max_storage_gb != -1 else float('inf'),
        'bookings_count': subscription.bookings_this_month,
        'bookings_limit': subscription.plan.max_bookings_per_month,
    }
    
    # Get recent payments
    recent_payments = SubscriptionPayment.objects.filter(
        subscription=subscription
    ).order_by('-created_at')[:5]
    
    # Calculate usage percentages
    usage_stats['photos_percentage'] = min(
        (usage_stats['photos_uploaded'] / max(usage_stats['photos_limit'], 1)) * 100, 100
    ) if usage_stats['photos_limit'] != -1 else 0
    
    usage_stats['storage_percentage'] = min(
        (usage_stats['storage_used'] / max(usage_stats['storage_limit'], 1)) * 100, 100
    ) if usage_stats['storage_limit'] != float('inf') else 0
    
    usage_stats['bookings_percentage'] = min(
        (usage_stats['bookings_count'] / max(usage_stats['bookings_limit'], 1)) * 100, 100
    ) if usage_stats['bookings_limit'] != -1 else 0
    
    context = {
        'subscription': subscription,
        'usage_stats': usage_stats,
        'recent_payments': recent_payments,
        'available_plans': SubscriptionPlan.objects.filter(is_active=True).exclude(id=subscription.plan.id)
    }
    
    return render(request, 'payments/subscription_dashboard.html', context)

@login_required
@require_POST
def upgrade_subscription(request):
    """Handle subscription upgrade"""
    plan_name = request.POST.get('plan_name')
    billing_cycle = request.POST.get('billing_cycle', 'monthly')
    
    try:
        subscription, prorated_amount = SubscriptionService.upgrade_subscription(
            request.user, plan_name, billing_cycle
        )
        
        messages.success(request, f'Successfully upgraded to {subscription.plan.display_name}!')
        
        # In a real app, you'd redirect to payment processing here
        # For now, we'll just redirect back to dashboard
        return redirect('subscription_dashboard')
        
    except Exception as e:
        messages.error(request, f'Failed to upgrade subscription: {str(e)}')
        return redirect('pricing_page')

@login_required
def billing_history(request):
    """User's billing history"""
    try:
        subscription = request.user.subscription
        payments = SubscriptionPayment.objects.filter(
            subscription=subscription
        ).order_by('-created_at')
    except UserSubscription.DoesNotExist:
        subscription = None
        payments = []
    
    context = {
        'subscription': subscription,
        'payments': payments
    }
    
    return render(request, 'payments/billing_history.html', context)

@login_required
def transaction_history(request):
	transactions = Transaction.objects.filter(user=request.user)
	return render(request, 'payments/transaction_history.html', {'transactions': transactions})

@login_required
def earnings_dashboard(request):
	if request.user.role != 'photographer':
		return render(request, 'payments/earnings_dashboard.html', {
			'total_earnings': 0, 
			'transactions': [],
			'paid_count': 0,
			'pending_count': 0,
			'failed_count': 0,
			'total_count': 0,
			'success_rate': 0,
			'average_per_transaction': 0,
			'monthly_earnings': [],
			'this_month_earnings': 0,
			'currency_symbol': 'RWF',
		})
	
	# Get all transactions for this photographer
	all_transactions = Transaction.objects.filter(booking__photographer=request.user)
	paid_transactions = all_transactions.filter(status='paid')
	pending_transactions = all_transactions.filter(status='pending')
	failed_transactions = all_transactions.filter(status='failed')
	
	# Calculate totals
	total_earnings = paid_transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0')
	paid_count = paid_transactions.count()
	pending_count = pending_transactions.count()
	failed_count = failed_transactions.count()
	total_count = all_transactions.count()
	
	# Calculate rates and averages
	success_rate = (paid_count / total_count * 100) if total_count > 0 else 0
	average_per_transaction = total_earnings / paid_count if paid_count > 0 else Decimal('0')
	
	# Calculate monthly earnings for the last 6 months
	today = datetime.now()
	monthly_earnings = []
	month_names = []
	
	for i in range(5, -1, -1):  # Last 6 months
		month_date = today - timedelta(days=30*i)
		month_start = month_date.replace(day=1)
		
		if i == 0:  # Next month
			next_month = month_start.replace(month=month_start.month + 1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1)
			month_end = next_month - timedelta(days=1)
		else:
			next_month = month_start.replace(month=month_start.month + 1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1)
			month_end = next_month - timedelta(days=1)
		
		month_earnings = paid_transactions.filter(
			created_at__gte=month_start,
			created_at__lte=month_end
		).aggregate(total=Sum('amount'))['total'] or Decimal('0')
		
		monthly_earnings.append(float(month_earnings))
		month_names.append(month_date.strftime('%b'))
	
	# This month's earnings
	current_month_start = today.replace(day=1)
	this_month_earnings = paid_transactions.filter(
		created_at__gte=current_month_start
	).aggregate(total=Sum('amount'))['total'] or Decimal('0')
	
	# Get recent transactions (limit to 10 for display)
	recent_transactions = paid_transactions.order_by('-created_at')[:10]
	
	return render(request, 'payments/earnings_dashboard.html', {
		'total_earnings': total_earnings,
		'transactions': recent_transactions,
		'all_transactions': all_transactions,
		'paid_count': paid_count,
		'pending_count': pending_count,
		'failed_count': failed_count,
		'total_count': total_count,
		'success_rate': success_rate,
		'average_per_transaction': average_per_transaction,
		'monthly_earnings': monthly_earnings,
		'month_names': month_names,
		'this_month_earnings': this_month_earnings,
		'currency_symbol': 'RWF',
	})

@csrf_exempt
@require_POST
def process_payment(request):
	"""Process payment and send notifications"""
	try:
		booking_id = request.POST.get('booking_id')
		amount = request.POST.get('amount')
		payment_method = request.POST.get('payment_method', 'Irembo Pay')
		
		if not booking_id or not amount:
			return JsonResponse({'error': 'Missing required fields'}, status=400)
			
		booking = get_object_or_404(Booking, id=booking_id)
		
		# Create transaction
		transaction = Transaction.objects.create(
			booking=booking,
			user=booking.client or User.objects.get(email=booking.client_email),
			amount=amount,
			transaction_id=str(uuid.uuid4())[:20],
			status='pending',
			payment_method=payment_method
		)
		
		# Simulate payment processing (replace with actual payment gateway)
		# For demo, randomly succeed/fail
		import random
		payment_success = random.choice([True, True, True, False])  # 75% success rate
		
		if payment_success:
			transaction.status = 'paid'
			transaction.save()
			
			# Update booking status
			booking.payment_status = 'paid'
			booking.status = 'confirmed'
			booking.save()
			
			# Send success email notification
			EmailService.send_payment_notification(transaction, 'success')
			
			# Also notify photographer
			EmailService.send_booking_notification(booking, 'confirmed', 'photographer')
			
			logger.info(f"Payment successful for booking {booking_id}, transaction {transaction.transaction_id}")
			
			return JsonResponse({
				'success': True, 
				'message': 'Payment successful!',
				'transaction_id': transaction.transaction_id
			})
		else:
			transaction.status = 'failed'
			transaction.save()
			
			# Send failure email notification
			EmailService.send_payment_notification(transaction, 'failed')
			
			logger.warning(f"Payment failed for booking {booking_id}, transaction {transaction.transaction_id}")
			
			return JsonResponse({
				'success': False,
				'message': 'Payment failed. Please try again.',
				'transaction_id': transaction.transaction_id
			})
			
	except Exception as e:
		logger.error(f"Error processing payment: {e}")
		return JsonResponse({'error': 'Payment processing error'}, status=500)

@login_required
def retry_payment(request, transaction_id):
	"""Allow user to retry failed payment"""
	transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
	
	if transaction.status != 'failed':
		messages.error(request, 'This transaction cannot be retried.')
		return redirect('transaction_history')
	
	# Create new transaction for retry
	new_transaction = Transaction.objects.create(
		booking=transaction.booking,
		user=transaction.user,
		amount=transaction.amount,
		transaction_id=str(uuid.uuid4())[:20],
		status='pending',
		payment_method=transaction.payment_method
	)
	
	# Redirect to payment page or process immediately
	messages.info(request, 'Payment retry initiated. Please complete the payment.')
	return redirect('process_payment')


# New Checkout Views
@login_required
def payment_checkout(request, booking_id):
	"""Display payment checkout page for a booking"""
	booking = get_object_or_404(Booking, id=booking_id)
	
	# Check if user is authorized to pay for this booking
	if booking.client and booking.client != request.user:
		messages.error(request, 'You are not authorized to pay for this booking.')
		return redirect('bookings:client_dashboard')
	
	# Check if already paid
	if booking.payment_status == 'paid':
		messages.info(request, 'This booking has already been paid.')
		return redirect('bookings:client_dashboard')
	
	# Calculate amount (you can add pricing logic here)
	# For now, using photographer's price or a default
	amount = booking.photographer.price or Decimal('50000')  # Default 50,000 RWF
	
	context = {
		'booking': booking,
		'amount': amount,
	}
	
	return render(request, 'payments/checkout.html', context)


@login_required
@require_POST
def process_booking_payment(request, booking_id):
	"""Process payment for a booking"""
	booking = get_object_or_404(Booking, id=booking_id)
	payment_method = request.POST.get('payment_method')
	
	# Check authorization
	if booking.client and booking.client != request.user:
		return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
	
	# Check if already paid
	if booking.payment_status == 'paid':
		return JsonResponse({'success': False, 'error': 'Already paid'}, status=400)
	
	amount = booking.photographer.price or Decimal('50000')
	
	# Extract payment method specific details
	payment_details = {
		'payment_method': payment_method,
		'customer_email': request.user.email
	}
	
	# Card payment details
	if payment_method == 'stripe':
		card_number = request.POST.get('card_number', '').replace(' ', '')
		payment_details.update({
			'card_last_four': card_number[-4:] if len(card_number) >= 4 else '',
			'cardholder_name': request.POST.get('cardholder_name', ''),
			'card_expiry': request.POST.get('card_expiry', ''),
			'card_cvv': request.POST.get('card_cvv', ''),
		})
	
	# Mobile Money details
	elif payment_method == 'mobile_money':
		payment_details.update({
			'mobile_money_provider': request.POST.get('momo_provider', ''),
			'mobile_money_phone': request.POST.get('momo_phone', ''),
		})
	
	# PayPal details
	elif payment_method == 'paypal':
		payment_details.update({
			'paypal_email': request.POST.get('paypal_email', ''),
		})
	
	# Bank Transfer details
	elif payment_method == 'bank_transfer':
		payment_details.update({
			'bank_reference': request.POST.get('bank_reference', ''),
		})
	
	# Use payment service
	from .services import PaymentService
	payment_service = PaymentService()
	
	result = payment_service.process_client_payment(
		booking_id=booking.id,
		amount=amount,
		payment_method=payment_method,
		customer_email=request.user.email,
		payment_details=payment_details
	)
	
	if result['success']:
		# Redirect to success page
		messages.success(request, 'Payment successful!')
		return redirect('payment_success', transaction_id=result['transaction_id'])
	else:
		messages.error(request, f'Payment failed: {result.get("error", "Unknown error")}')
		return redirect('payment_failed', booking_id=booking.id)


def payment_success(request, transaction_id):
	"""Display payment success page"""
	try:
		transaction = Transaction.objects.get(transaction_id=transaction_id)
		context = {
			'transaction_id': transaction_id,
			'amount': transaction.amount,
			'payment_method': transaction.payment_method,
			'booking': transaction.booking,
		}
		return render(request, 'payments/payment_success.html', context)
	except Transaction.DoesNotExist:
		messages.error(request, 'Transaction not found.')
		return redirect('home')


def payment_failed(request, booking_id):
	"""Display payment failure page"""
	try:
		booking = Booking.objects.get(id=booking_id)
		error_message = request.GET.get('error', 'Payment could not be processed')
		context = {
			'booking': booking,
			'error_message': error_message,
		}
		return render(request, 'payments/payment_failed.html', context)
	except Booking.DoesNotExist:
		messages.error(request, 'Booking not found.')
		return redirect('home')


# Subscription Payment Views
@login_required
def subscription_checkout(request, plan_id):
	"""Display subscription payment checkout"""
	plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
	
	context = {
		'plan': plan,
	}
	
	return render(request, 'payments/subscription_checkout.html', context)


@login_required
@require_POST
def subscription_payment_process(request):
	"""Process subscription payment"""
	plan_id = request.POST.get('plan_id')
	billing_cycle = request.POST.get('billing_cycle', 'monthly')
	payment_method = request.POST.get('payment_method')
	
	plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
	
	# Calculate amount based on billing cycle
	if billing_cycle == 'yearly':
		amount = plan.get_yearly_price()
	else:
		amount = plan.price_monthly
	
	# Create or get user subscription
	try:
		subscription = request.user.subscription
		# Upgrade subscription
		from .services import SubscriptionService
		subscription_service = SubscriptionService()
		subscription, prorated_amount = subscription_service.upgrade_subscription(
			request.user, plan.name, billing_cycle
		)
	except UserSubscription.DoesNotExist:
		# Create new subscription
		from datetime import timedelta
		from django.utils import timezone
		
		end_date = timezone.now() + timedelta(days=365 if billing_cycle == 'yearly' else 30)
		subscription = UserSubscription.objects.create(
			user=request.user,
			plan=plan,
			billing_cycle=billing_cycle,
			status='active',
			end_date=end_date,
			next_billing_date=end_date
		)
	
	# Create subscription payment record
	from datetime import timedelta
	from django.utils import timezone
	
	billing_start = timezone.now()
	billing_end = billing_start + timedelta(days=365 if billing_cycle == 'yearly' else 30)
	
	# Build payment record with method-specific details
	payment_data = {
		'subscription': subscription,
		'amount': amount,
		'billing_period_start': billing_start,
		'billing_period_end': billing_end,
		'payment_method': payment_method,
		'payment_gateway': 'stripe' if payment_method == 'stripe' else 'other',
		'status': 'completed'  # In production, this would be 'pending' until confirmed
	}
	
	# Add payment method specific details
	if payment_method == 'stripe':
		card_number = request.POST.get('card_number', '').replace(' ', '')
		payment_data.update({
			'card_last_four': card_number[-4:] if len(card_number) >= 4 else '',
			'cardholder_name': request.POST.get('cardholder_name', ''),
			'card_brand': 'Unknown',  # Would be detected from card number in production
		})
	elif payment_method == 'mobile_money':
		payment_data.update({
			'mobile_money_provider': request.POST.get('momo_provider', ''),
			'mobile_money_phone': request.POST.get('momo_phone', ''),
		})
	elif payment_method == 'paypal':
		payment_data.update({
			'paypal_email': request.POST.get('paypal_email', ''),
		})
	
	payment = SubscriptionPayment.objects.create(**payment_data)
	
	# Mark subscription as active
	subscription.status = 'active'
	subscription.last_payment_date = timezone.now()
	subscription.save()
	
	messages.success(request, f'Successfully subscribed to {plan.display_name}!')
	return redirect('subscription_dashboard')
