
from django.db import models
from users.models import User

class Booking(models.Model):
	STATUS_CHOICES = [
		('pending', 'Pending'),
		('confirmed', 'Confirmed'),
		('completed', 'Completed'),
		('cancelled', 'Cancelled'),
	]
	PAYMENT_STATUS_CHOICES = [
		('pending', 'Pending'),
		('paid', 'Paid'),
		('failed', 'Failed'),
	]
	client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_bookings', limit_choices_to={'role': 'client'})
	photographer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photographer_bookings', limit_choices_to={'role': 'photographer'})
	service_type = models.CharField(max_length=100)
	date = models.DateField()
	time = models.TimeField()
	location = models.CharField(max_length=255)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
	payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Booking: {self.client.email} with {self.photographer.email} on {self.date}"
