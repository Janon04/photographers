
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Transaction
from bookings.models import Booking
from users.models import User

@login_required
def transaction_history(request):
	transactions = Transaction.objects.filter(user=request.user)
	return render(request, 'payments/transaction_history.html', {'transactions': transactions})

@login_required
def earnings_dashboard(request):
	if request.user.role != 'photographer':
		return render(request, 'payments/earnings_dashboard.html', {'total_earnings': 0, 'transactions': []})
	transactions = Transaction.objects.filter(booking__photographer=request.user, status='paid')
	total_earnings = sum(t.amount for t in transactions)
	return render(request, 'payments/earnings_dashboard.html', {'total_earnings': total_earnings, 'transactions': transactions})
