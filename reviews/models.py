
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json
from datetime import datetime, timedelta
from users.models import User
from bookings.models import Booking


class ReviewCategory(models.Model):
    """Categories for different aspects of photography services"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Review Categories"
    
    def __str__(self):
        return self.name


class Review(models.Model):
    """Enhanced Review model with comprehensive analysis capabilities"""
    
    # Core Review Information
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review', null=True, blank=True)
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_made', null=True, blank=True)
    photographer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    
    # Anonymous reviewer fields
    anonymous_name = models.CharField(max_length=100, blank=True, default='Anonymous', help_text="Name for anonymous reviews")
    anonymous_email = models.EmailField(blank=True, help_text="Optional email for anonymous reviews")
    
    # Rating System
    overall_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5,
        help_text="Overall rating from 1-5 stars"
    )
    
    # Detailed Ratings
    quality_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5,
        help_text="Photo quality rating"
    )
    professionalism_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5,
        help_text="Professionalism rating"
    )
    communication_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5,
        help_text="Communication rating"
    )
    value_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5,
        help_text="Value for money rating"
    )
    
    # Review Content
    title = models.CharField(max_length=200, default="Great Service", help_text="Review title/summary")
    comment = models.TextField(help_text="Detailed review comment")
    categories = models.ManyToManyField(ReviewCategory, blank=True, help_text="Review categories")
    
    # Review Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False, help_text='Admin must approve before public display.')
    is_featured = models.BooleanField(default=False, help_text='Featured review for homepage')
    is_verified = models.BooleanField(default=True, help_text='Verified booking review')
    
    # Interaction Tracking
    helpfulness_votes = models.PositiveIntegerField(default=0)
    total_votes = models.PositiveIntegerField(default=0)
    
    # Analytics Fields
    word_count = models.PositiveIntegerField(default=0)
    reading_time_seconds = models.PositiveIntegerField(default=0)
    
    # Legacy field for backward compatibility
    rating = models.PositiveSmallIntegerField(default=5)  # Maps to overall_rating
    
    # AI Analysis Fields
    ai_sentiment = models.CharField(
        max_length=20,
        choices=[
            ('positive', 'Positive'),
            ('negative', 'Negative'),
            ('neutral', 'Neutral'),
            ('mixed', 'Mixed')
        ],
        default='neutral',
        help_text="AI-determined sentiment"
    )
    sentiment_confidence = models.FloatField(default=0.0, help_text="Confidence score 0-1")
    sentiment_analysis = models.JSONField(default=dict, blank=True, help_text="Detailed AI analysis")
    key_phrases = models.JSONField(default=list, blank=True, help_text="Extracted key phrases")
    rating_consistency = models.BooleanField(default=True, help_text="Rating matches sentiment")
    
    analysis_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Analysis'),
            ('completed', 'Analysis Complete'),
            ('failed', 'Analysis Failed')
        ],
        default='pending'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['photographer', '-created_at']),
            models.Index(fields=['overall_rating']),
            models.Index(fields=['ai_sentiment']),
            models.Index(fields=['is_approved', '-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Sync legacy rating field
        if self.overall_rating:
            self.rating = self.overall_rating
        elif self.rating:
            self.overall_rating = self.rating
            
        # Calculate word count and reading time
        if self.comment:
            self.word_count = len(self.comment.split())
            self.reading_time_seconds = max(10, self.word_count * 0.5)  # ~2 words per second
            
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        # Run sentiment analysis for new reviews
        if is_new and self.comment:
            self.analyze_sentiment()
    
    def analyze_sentiment(self):
        """Run AI sentiment analysis on the review"""
        try:
            from config.ai_service import ai_service
            
            # Prepare review data for analysis
            review_data = {
                'title': self.title,
                'comment': self.comment,
                'overall_rating': self.overall_rating,
                'quality_rating': self.quality_rating,
                'professionalism_rating': self.professionalism_rating,
                'communication_rating': self.communication_rating,
                'value_rating': self.value_rating,
            }
            
            # Run comprehensive sentiment analysis
            sentiment_result = ai_service.analyze_review_sentiment(
                review_data, 
                include_detailed_analysis=True
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
    
    def get_average_detailed_rating(self):
        """Calculate average of all detailed ratings"""
        ratings = [
            self.quality_rating,
            self.professionalism_rating,
            self.communication_rating,
            self.value_rating
        ]
        return round(sum(ratings) / len(ratings), 1)
    
    def get_helpfulness_percentage(self):
        """Calculate helpfulness percentage"""
        if self.total_votes == 0:
            return 0
        return round((self.helpfulness_votes / self.total_votes) * 100, 1)
    
    def is_recent(self, days=30):
        """Check if review is recent"""
        return self.created_at >= timezone.now() - timedelta(days=days)
    
    def get_sentiment_color(self):
        """Get color for sentiment display"""
        colors = {
            'positive': '#4CAF50',
            'negative': '#F44336',
            'neutral': '#FF9800',
            'mixed': '#9C27B0'
        }
        return colors.get(self.ai_sentiment, '#9E9E9E')
    
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
            'impact_score': self.overall_rating * 0.2 + positive_count * 0.1 - negative_count * 0.1
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
            self.overall_rating <= 2
        )
    
    # Like/Dislike and Comment Methods
    def get_like_count(self):
        """Get total number of likes"""
        stats, created = ReviewLikeStats.objects.get_or_create(review=self)
        if created:
            stats.update_stats()
        return stats.total_likes
    
    def get_dislike_count(self):
        """Get total number of dislikes"""
        stats, created = ReviewLikeStats.objects.get_or_create(review=self)
        if created:
            stats.update_stats()
        return stats.total_dislikes
    
    def get_comment_count(self):
        """Get total number of approved comments"""
        stats, created = ReviewLikeStats.objects.get_or_create(review=self)
        if created:
            stats.update_stats()
        return stats.total_comments
    
    def get_user_vote(self, user):
        """Get user's vote on this review"""
        if not user.is_authenticated:
            return None
        try:
            vote = ReviewHelpfulness.objects.get(review=self, user=user)
            return vote.vote_type
        except ReviewHelpfulness.DoesNotExist:
            return None
    
    def toggle_like(self, user):
        """Toggle like status for a user"""
        if not user.is_authenticated:
            return False
        
        vote, created = ReviewHelpfulness.objects.get_or_create(
            review=self,
            user=user,
            defaults={'vote_type': 'like', 'is_helpful': True}
        )
        
        if not created:
            if vote.vote_type == 'like':
                # Remove like
                vote.delete()
            else:
                # Change to like
                vote.vote_type = 'like'
                vote.is_helpful = True
                vote.save()
        
        # Update statistics
        stats, created = ReviewLikeStats.objects.get_or_create(review=self)
        stats.update_stats()
        
        return True
    
    def toggle_dislike(self, user):
        """Toggle dislike status for a user"""
        if not user.is_authenticated:
            return False
        
        vote, created = ReviewHelpfulness.objects.get_or_create(
            review=self,
            user=user,
            defaults={'vote_type': 'dislike', 'is_helpful': False}
        )
        
        if not created:
            if vote.vote_type == 'dislike':
                # Remove dislike
                vote.delete()
            else:
                # Change to dislike
                vote.vote_type = 'dislike'
                vote.is_helpful = False
                vote.save()
        
        # Update statistics
        stats, created = ReviewLikeStats.objects.get_or_create(review=self)
        stats.update_stats()
        
        return True
    
    def add_comment(self, user, comment_text, parent_comment=None, anonymous_name=None, anonymous_email=None):
        """Add a comment to this review"""
        comment = ReviewComment.objects.create(
            review=self,
            commenter=user if user.is_authenticated else None,
            comment_text=comment_text,
            parent_comment=parent_comment,
            anonymous_name=anonymous_name or '',
            anonymous_email=anonymous_email or ''
        )
        
        # Update statistics
        stats, created = ReviewLikeStats.objects.get_or_create(review=self)
        stats.update_stats()
        
        return comment
    
    def get_engagement_score(self):
        """Calculate engagement score based on likes, dislikes, and comments"""
        likes = self.get_like_count()
        dislikes = self.get_dislike_count()
        comments = self.get_comment_count()
        
        # Weighted engagement score
        return (likes * 2) + (comments * 1.5) + (dislikes * 0.5)

    def __str__(self):
        reviewer_name = self.reviewer.get_full_name() if self.reviewer else self.anonymous_name
        return f'Review by {reviewer_name} for {self.photographer} - {self.overall_rating}★'
    
    @property
    def reviewer_display_name(self):
        """Get display name for reviewer (handles anonymous reviews)"""
        if self.reviewer:
            return self.reviewer.get_full_name() or self.reviewer.username
        return self.anonymous_name or 'Anonymous'
    
    @property
    def is_anonymous(self):
        """Check if this is an anonymous review"""
        return self.reviewer is None


class ReviewHelpfulness(models.Model):
    """Track user votes on review helpfulness - Enhanced with like/dislike system"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpfulness_votes_detail')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_helpful = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Enhanced fields for like/dislike system
    vote_type = models.CharField(
        max_length=15,
        choices=[
            ('like', 'Like'),
            ('dislike', 'Dislike'),
            ('helpful', 'Helpful'),
            ('not_helpful', 'Not Helpful')
        ],
        default='helpful'
    )
    
    class Meta:
        unique_together = ('review', 'user')
        indexes = [
            models.Index(fields=['review', 'vote_type']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f'{self.user} voted {self.vote_type} on {self.review}'


class ReviewComment(models.Model):
    """Comments on reviews - allowing discussion"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='comments')
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_comments')
    comment_text = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=True)
    parent_comment = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies'
    )
    
    # Anonymous commenter support
    anonymous_name = models.CharField(max_length=100, blank=True)
    anonymous_email = models.EmailField(blank=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['review', 'created_at']),
            models.Index(fields=['commenter', 'created_at']),
        ]
    
    def __str__(self):
        commenter_name = self.commenter.get_full_name() if self.commenter else self.anonymous_name
        return f'Comment by {commenter_name} on {self.review}'
    
    @property
    def commenter_display_name(self):
        """Get display name for commenter"""
        if self.commenter:
            return self.commenter.get_full_name() or self.commenter.username
        return self.anonymous_name or 'Anonymous'
    
    @property
    def is_anonymous(self):
        """Check if this is an anonymous comment"""
        return self.commenter is None


class ReviewLikeStats(models.Model):
    """Cached statistics for review likes/dislikes"""
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name='like_stats')
    total_likes = models.PositiveIntegerField(default=0)
    total_dislikes = models.PositiveIntegerField(default=0)
    total_helpful_votes = models.PositiveIntegerField(default=0)
    total_not_helpful_votes = models.PositiveIntegerField(default=0)
    total_comments = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['total_likes']),
            models.Index(fields=['total_dislikes']),
        ]
    
    def update_stats(self):
        """Recalculate all statistics"""
        votes = ReviewHelpfulness.objects.filter(review=self.review)
        
        self.total_likes = votes.filter(vote_type='like').count()
        self.total_dislikes = votes.filter(vote_type='dislike').count()
        self.total_helpful_votes = votes.filter(vote_type='helpful').count()
        self.total_not_helpful_votes = votes.filter(vote_type='not_helpful').count()
        self.total_comments = ReviewComment.objects.filter(review=self.review, is_approved=True).count()
        
        self.save()
    
    def __str__(self):
        return f'Stats for {self.review}: {self.total_likes} likes, {self.total_dislikes} dislikes'


class ReviewResponse(models.Model):
    """Photographer responses to reviews"""
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name='photographer_response')
    response_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=True)
    
    def __str__(self):
        return f'Response to review by {self.review.reviewer}'


class ReviewAnalytics(models.Model):
    """Analytics data for reviews"""
    photographer = models.OneToOneField(User, on_delete=models.CASCADE, related_name='review_analytics')
    
    # Rating Statistics
    total_reviews = models.PositiveIntegerField(default=0)
    average_overall_rating = models.FloatField(default=0.0)
    average_quality_rating = models.FloatField(default=0.0)
    average_professionalism_rating = models.FloatField(default=0.0)
    average_communication_rating = models.FloatField(default=0.0)
    average_value_rating = models.FloatField(default=0.0)
    
    # Sentiment Statistics
    positive_sentiment_count = models.PositiveIntegerField(default=0)
    negative_sentiment_count = models.PositiveIntegerField(default=0)
    neutral_sentiment_count = models.PositiveIntegerField(default=0)
    
    # Engagement Statistics
    total_helpfulness_votes = models.PositiveIntegerField(default=0)
    response_rate = models.FloatField(default=0.0)  # Percentage of reviews responded to
    
    # Trend Analysis
    rating_trend = models.CharField(max_length=20, default='stable')  # improving, declining, stable
    sentiment_trend = models.CharField(max_length=20, default='stable')
    
    # Last Updated
    last_calculated = models.DateTimeField(auto_now=True)
    
    def update_analytics(self):
        """Recalculate all analytics for this photographer"""
        from django.db.models import Avg, Count
        
        reviews = Review.objects.filter(photographer=self.photographer, is_approved=True)
        
        if reviews.exists():
            # Rating averages
            averages = reviews.aggregate(
                avg_overall=Avg('overall_rating'),
                avg_quality=Avg('quality_rating'),
                avg_professionalism=Avg('professionalism_rating'),
                avg_communication=Avg('communication_rating'),
                avg_value=Avg('value_rating')
            )
            
            self.total_reviews = reviews.count()
            self.average_overall_rating = round(averages['avg_overall'] or 0, 2)
            self.average_quality_rating = round(averages['avg_quality'] or 0, 2)
            self.average_professionalism_rating = round(averages['avg_professionalism'] or 0, 2)
            self.average_communication_rating = round(averages['avg_communication'] or 0, 2)
            self.average_value_rating = round(averages['avg_value'] or 0, 2)
            
            # Sentiment counts
            sentiment_counts = reviews.values('ai_sentiment').annotate(count=Count('id'))
            sentiment_dict = {item['ai_sentiment']: item['count'] for item in sentiment_counts}
            
            self.positive_sentiment_count = sentiment_dict.get('positive', 0)
            self.negative_sentiment_count = sentiment_dict.get('negative', 0)
            self.neutral_sentiment_count = sentiment_dict.get('neutral', 0)
            
            # Response rate
            responses_count = ReviewResponse.objects.filter(review__photographer=self.photographer).count()
            self.response_rate = round((responses_count / self.total_reviews) * 100, 1) if self.total_reviews > 0 else 0
            
            # Calculate trends (simplified)
            recent_reviews = reviews.filter(created_at__gte=timezone.now() - timedelta(days=30))
            older_reviews = reviews.filter(created_at__lt=timezone.now() - timedelta(days=30))
            
            if recent_reviews.exists() and older_reviews.exists():
                recent_avg = recent_reviews.aggregate(avg=Avg('overall_rating'))['avg']
                older_avg = older_reviews.aggregate(avg=Avg('overall_rating'))['avg']
                
                if recent_avg > older_avg + 0.2:
                    self.rating_trend = 'improving'
                elif recent_avg < older_avg - 0.2:
                    self.rating_trend = 'declining'
                else:
                    self.rating_trend = 'stable'
        
        self.save()
    
    def get_sentiment_distribution(self):
        """Get sentiment distribution as percentages"""
        total = self.positive_sentiment_count + self.negative_sentiment_count + self.neutral_sentiment_count
        if total == 0:
            return {'positive': 0, 'negative': 0, 'neutral': 0}
        
        return {
            'positive': round((self.positive_sentiment_count / total) * 100, 1),
            'negative': round((self.negative_sentiment_count / total) * 100, 1),
            'neutral': round((self.neutral_sentiment_count / total) * 100, 1)
        }
    
    def __str__(self):
        return f'Analytics for {self.photographer} - {self.total_reviews} reviews'
