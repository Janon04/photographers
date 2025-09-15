
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
	client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_bookings', limit_choices_to={'role': 'client'}, null=True, blank=True)
	photographer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photographer_bookings', limit_choices_to={'role': 'photographer'})
	service_type = models.CharField(max_length=100)
	date = models.DateField()
	time = models.TimeField()
	location = models.CharField(max_length=255)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
	payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
	created_at = models.DateTimeField(auto_now_add=True)
	client_name = models.CharField(max_length=100, blank=True, null=True)
	client_email = models.EmailField(blank=True, null=True)
	client_phone = models.CharField(max_length=30, blank=True, null=True)

	def __str__(self):
		client_email = self.client.email if self.client else (self.client_email or self.client_name or 'Anonymous')
		photographer_email = self.photographer.email if self.photographer else 'Unknown'
		return f"Booking: {client_email} with {photographer_email} on {self.date}"
