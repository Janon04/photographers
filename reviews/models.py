
from django.db import models

from users.models import User
from bookings.models import Booking

class Review(models.Model):
	booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
	reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_made')
	photographer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
	rating = models.PositiveSmallIntegerField()
	comment = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f'Review by {self.reviewer} for {self.photographer}'
