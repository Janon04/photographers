
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from decimal import Decimal
from .models import Transaction
from bookings.models import Booking
from users.models import User
from config.email_service import EmailService
import logging
import uuid

logger = logging.getLogger(__name__)

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
