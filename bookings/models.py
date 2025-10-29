
from django.db import models
from users.models import User
import json
from decimal import Decimal

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
	
	def simulate_ai_pricing(self):
		"""Simulate AI pricing for demo purposes"""
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
		
		base_price = base_rates.get(self.service_type.lower(), 500)
		
		return {
			'suggested_price': base_price,
			'price_range': {'min': int(base_price * 0.8), 'max': int(base_price * 1.2)},
			'factors_considered': [
				f"Base {self.service_type} rate: ${base_price}",
				"Market analysis applied",
				"Experience level considered"
			],
			'recommendations': [
				"Consider package deals for repeat clients",
				"Add travel fees for distant locations"
			]
		}
	
	def get_pricing_recommendations(self):
		"""Get AI pricing recommendations"""
		pricing = self.simulate_ai_pricing()
		return pricing.get('recommendations', [])
	
	def get_market_analysis(self):
		"""Get market analysis for this booking"""
		return {
			'demand_level': 'moderate',
			'competition': 'average',
			'seasonal_factor': 'normal'
		}
	
	def get_price_range(self):
		"""Get suggested price range"""
		pricing = self.simulate_ai_pricing()
		return pricing.get('price_range', {'min': 400, 'max': 600})

	def __str__(self):
		client_email = self.client.email if self.client else (self.client_email or self.client_name or 'Anonymous')
		photographer_email = self.photographer.email if self.photographer else 'Unknown'
		return f"Booking: {client_email} with {photographer_email} on {self.date}"
