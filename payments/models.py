
from django.db import models
from users.models import User
from bookings.models import Booking

class Transaction(models.Model):
	booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='transactions')
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	transaction_id = models.CharField(max_length=100, unique=True)
	status = models.CharField(max_length=20)
	payment_method = models.CharField(max_length=50, default='Irembo Pay')
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Transaction {self.transaction_id} for {self.user.email}"
