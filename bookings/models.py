
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
	
	SERVICE_TYPE_CHOICES = [
		('wedding', '💍 Wedding Photography'),
		('engagement', '💕 Engagement Session'),
		('portrait', '👨‍👩‍👧‍👦 Family Portrait'),
		('maternity', '🤰 Maternity Photography'),
		('newborn', '👶 Newborn Photography'),
		('children', '🧒 Children Photography'),
		('headshots', '💼 Professional Headshots'),
		('corporate', '🏢 Corporate Events'),
		('business', '💼 Business Photography'),
		('conference', '🎤 Conference Photography'),
		('product', '📦 Product Photography'),
		('commercial', '🏭 Commercial Photography'),
		('real_estate', '🏠 Real Estate Photography'),
		('food', '🍽️ Food Photography'),
		('fashion', '👗 Fashion Photography'),
		('lifestyle', '✨ Lifestyle Photography'),
		('travel', '✈️ Travel Photography'),
		('landscape', '🏔️ Landscape Photography'),
		('nature', '🌿 Nature Photography'),
		('wildlife', '🦁 Wildlife Photography'),
		('sports', '⚽ Sports Photography'),
		('event', '🎉 Event Photography'),
		('party', '🎈 Party Photography'),
		('birthday', '🎂 Birthday Photography'),
		('graduation', '🎓 Graduation Photography'),
		('anniversary', '💏 Anniversary Photography'),
		('reunion', '👥 Family Reunion'),
		('cultural', '🎭 Cultural Events'),
		('religious', '⛪ Religious Ceremonies'),
		('artistic', '🎨 Artistic Photography'),
		('documentary', '📷 Documentary Photography'),
		('street', '🛣️ Street Photography'),
		('architecture', '🏛️ Architecture Photography'),
		('automotive', '🚗 Automotive Photography'),
		('aerial', '🚁 Aerial/Drone Photography'),
		('underwater', '🤿 Underwater Photography'),
		('macro', '🔍 Macro Photography'),
		('black_white', '⚫ Black & White Photography'),
		('vintage', '📸 Vintage Style Photography'),
		('custom', '🎯 Custom Photography Session'),
	]
	
	client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_bookings', limit_choices_to={'role': 'client'}, null=True, blank=True)
	photographer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photographer_bookings', limit_choices_to={'role': 'photographer'})
	service_type = models.CharField(max_length=100, choices=SERVICE_TYPE_CHOICES)
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
			# Premium Services
			'wedding': 1500,
			'engagement': 500,
			'commercial': 900,
			'corporate': 800,
			'business': 700,
			'aerial': 1200,
			'underwater': 1000,
			
			# Portrait & Family
			'portrait': 350,
			'maternity': 400,
			'newborn': 450,
			'children': 300,
			'headshots': 250,
			'family_reunion': 400,
			
			# Events & Celebrations
			'event': 650,
			'party': 500,
			'birthday': 400,
			'graduation': 350,
			'anniversary': 450,
			'cultural': 600,
			'religious': 550,
			'conference': 750,
			
			# Specialized Photography
			'fashion': 750,
			'lifestyle': 600,
			'product': 550,
			'food': 500,
			'real_estate': 400,
			'automotive': 650,
			'architecture': 500,
			
			# Artistic & Creative
			'artistic': 600,
			'documentary': 700,
			'street': 300,
			'black_white': 400,
			'vintage': 450,
			'macro': 350,
			
			# Nature & Outdoor
			'landscape': 400,
			'nature': 350,
			'wildlife': 600,
			'travel': 500,
			'sports': 500,
			
			# Custom
			'custom': 500,
		}
		
		base_price = base_rates.get(self.service_type.lower(), 500)
		
		return {
			'suggested_price': base_price,
			'price_range': {'min': int(base_price * 0.8), 'max': int(base_price * 1.2)},
			'factors_considered': [
				f"Base {self.service_type} rate: Rwf {base_price}",
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
