
from django.db import models
import json
from users.models import User
from bookings.models import Booking


class Review(models.Model):
	booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
	reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_made')
	photographer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
	rating = models.PositiveSmallIntegerField()
	comment = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	is_approved = models.BooleanField(default=False, help_text='Admin must approve before public display.')
	
	def simulate_sentiment_analysis(self):
		"""Simulate sentiment analysis for demo purposes"""
		import re
		
		# Simple sentiment analysis based on keywords
		positive_words = ['amazing', 'excellent', 'great', 'wonderful', 'fantastic', 'perfect', 'outstanding', 'love', 'awesome', 'beautiful', 'professional', 'recommend', 'brilliant', 'impressed', 'superb']
		negative_words = ['terrible', 'awful', 'bad', 'horrible', 'disappointing', 'unprofessional', 'late', 'poor', 'worst', 'rude', 'unsatisfied', 'complaint']
		
		comment_lower = self.comment.lower()
		positive_count = sum(1 for word in positive_words if word in comment_lower)
		negative_count = sum(1 for word in negative_words if word in comment_lower)
		
		# Calculate sentiment score
		if positive_count > negative_count:
			sentiment = 'positive'
		elif negative_count > positive_count:
			sentiment = 'negative'
		else:
			sentiment = 'neutral'
		
		# Extract key phrases (simple approach)
		sentences = re.split(r'[.!?]+', self.comment)
		key_phrases = [s.strip() for s in sentences if len(s.strip()) > 10][:3]
		
		return {
			'sentiment': sentiment,
			'confidence': min(0.95, 0.6 + (abs(positive_count - negative_count) * 0.1)),
			'key_phrases': key_phrases,
			'emotions': {
				'joy': positive_count * 0.2,
				'satisfaction': positive_count * 0.15,
				'disappointment': negative_count * 0.2,
				'frustration': negative_count * 0.15
			},
			'impact_score': self.rating * 0.2 + positive_count * 0.1 - negative_count * 0.1
		}
	
	def get_sentiment_label(self):
		"""Get sentiment analysis label"""
		analysis = self.simulate_sentiment_analysis()
		return analysis['sentiment']
	
	def get_key_phrases(self):
		"""Get extracted key phrases"""
		analysis = self.simulate_sentiment_analysis()
		return analysis.get('key_phrases', [])
	
	def get_impact_score(self):
		"""Get review impact score"""
		analysis = self.simulate_sentiment_analysis()
		return round(analysis.get('impact_score', 0), 2)
	
	def get_sentiment_emoji(self):
		"""Get emoji representation of sentiment"""
		sentiment = self.get_sentiment_label()
		if sentiment == 'positive':
			return '😊'
		elif sentiment == 'negative':
			return '😞'
		else:
			return '😐'
	analysis_status = models.CharField(
		max_length=20,
		choices=[
			('pending', 'Pending Analysis'),
			('completed', 'Analysis Complete'),
			('failed', 'Analysis Failed')
		],
		default='pending'
	)
	
	def save(self, *args, **kwargs):
		# Run sentiment analysis for new reviews
		if not self.pk and self.comment:
			super().save(*args, **kwargs)
			self.analyze_sentiment()
		else:
			super().save(*args, **kwargs)
	
	def analyze_sentiment(self):
		"""Run AI sentiment analysis on the review"""
		try:
			from config.ai_service import ai_service
			
			# Run sentiment analysis
			sentiment_result = ai_service.analyze_review_sentiment(
				self.comment, 
				self.rating
			)
			
			if 'error' not in sentiment_result:
				self.ai_sentiment = sentiment_result.get('sentiment', 'neutral')
				self.sentiment_confidence = sentiment_result.get('confidence', 0.0)
				self.sentiment_analysis = sentiment_result
				self.key_phrases = sentiment_result.get('key_phrases', [])
				self.rating_consistency = sentiment_result.get('rating_consistency', True)
				self.analysis_status = 'completed'
			else:
				self.analysis_status = 'failed'
			
			self.save(update_fields=[
				'ai_sentiment', 'sentiment_confidence', 'sentiment_analysis',
				'key_phrases', 'rating_consistency', 'analysis_status'
			])
			
		except Exception as e:
			import logging
			logger = logging.getLogger(__name__)
			logger.error(f"Sentiment analysis failed for review {self.id}: {str(e)}")
			self.analysis_status = 'failed'
			self.save(update_fields=['analysis_status'])
	
	def get_sentiment_insights(self):
		"""Get AI sentiment insights"""
		if self.sentiment_analysis:
			return self.sentiment_analysis.get('suggestions', [])
		return []
	
	def get_emotional_indicators(self):
		"""Get emotional indicators from analysis"""
		if self.sentiment_analysis:
			return self.sentiment_analysis.get('emotional_indicators', {})
		return {}
	
	def needs_attention(self):
		"""Check if review needs special attention"""
		return (
			self.ai_sentiment == 'negative' or 
			not self.rating_consistency or 
			self.rating <= 2
		)

	def __str__(self):
		return f'Review by {self.reviewer} for {self.photographer}'
