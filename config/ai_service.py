"""
PhotoRw AI Service - Intelligent Photography Platform Features
Provides smart photo categorization, pricing suggestions, and sentiment analysis
"""

import os
import logging
import json
import requests
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import re
from collections import Counter
import statistics

from django.conf import settings
from django.db.models import Avg, Count, Q
from django.core.cache import cache
from django.utils import timezone

# Configure logging
logger = logging.getLogger(__name__)

class PhotoRwAIService:
    """
    Comprehensive AI service for PhotoRw platform
    Handles photo analysis, pricing optimization, and sentiment analysis
    """
    
    def __init__(self):
        self.photo_categories = {
            'wedding': ['bride', 'groom', 'ceremony', 'reception', 'rings', 'bouquet', 'dress'],
            'portrait': ['face', 'person', 'headshot', 'family', 'individual', 'studio'],
            'event': ['party', 'celebration', 'corporate', 'conference', 'gathering'],
            'landscape': ['nature', 'scenery', 'outdoor', 'mountains', 'sunset', 'beach'],
            'commercial': ['product', 'business', 'advertising', 'brand', 'marketing'],
            'fashion': ['model', 'clothing', 'style', 'runway', 'designer', 'magazine'],
            'sports': ['action', 'athlete', 'game', 'competition', 'team', 'stadium'],
            'food': ['restaurant', 'cuisine', 'meal', 'recipe', 'chef', 'dining']
        }
        
        self.sentiment_indicators = {
            'positive': ['excellent', 'amazing', 'professional', 'beautiful', 'perfect', 'love', 'stunning', 'fantastic', 'wonderful', 'outstanding'],
            'negative': ['poor', 'bad', 'terrible', 'disappointing', 'unprofessional', 'late', 'rude', 'awful', 'horrible', 'worst'],
            'neutral': ['okay', 'average', 'decent', 'acceptable', 'standard', 'normal', 'fine', 'regular']
        }
        
        self.pricing_factors = {
            'base_rates': {
                'wedding': 1500,
                'portrait': 300,
                'event': 800,
                'landscape': 400,
                'commercial': 1200,
                'fashion': 1000,
                'sports': 600,
                'food': 500
            },
            'experience_multiplier': {
                'beginner': 0.7,
                'intermediate': 1.0,
                'advanced': 1.3,
                'expert': 1.6
            },
            'market_factors': {
                'high_demand': 1.2,
                'normal_demand': 1.0,
                'low_demand': 0.8
            }
        }
    
    def analyze_photo_content(self, image_path: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        Analyze photo content and suggest categories
        Uses filename, metadata, and basic image analysis
        """
        try:
            analysis_result = {
                'categories': [],
                'confidence_scores': {},
                'suggested_tags': [],
                'technical_analysis': {},
                'recommendations': []
            }
            
            # Extract filename for analysis
            filename = os.path.basename(image_path).lower()
            
            # Category detection based on filename and metadata
            for category, keywords in self.photo_categories.items():
                score = 0
                matched_keywords = []
                
                for keyword in keywords:
                    if keyword in filename:
                        score += 1
                        matched_keywords.append(keyword)
                
                # Check metadata if provided
                if metadata:
                    description = str(metadata.get('description', '')).lower()
                    title = str(metadata.get('title', '')).lower()
                    for keyword in keywords:
                        if keyword in description or keyword in title:
                            score += 0.5
                            matched_keywords.append(keyword)
                
                if score > 0:
                    confidence = min(score / len(keywords), 1.0)
                    analysis_result['categories'].append(category)
                    analysis_result['confidence_scores'][category] = confidence
                    analysis_result['suggested_tags'].extend(matched_keywords)
            
            # Remove duplicates from tags
            analysis_result['suggested_tags'] = list(set(analysis_result['suggested_tags']))
            
            # Technical analysis (simulated)
            analysis_result['technical_analysis'] = {
                'estimated_quality': 'high' if 'professional' in filename or 'hd' in filename else 'medium',
                'suggested_editing': self._suggest_photo_editing(filename),
                'seo_keywords': self._generate_seo_keywords(analysis_result['categories'])
            }
            
            # Generate recommendations
            analysis_result['recommendations'] = self._generate_photo_recommendations(analysis_result)
            
            logger.info(f"Photo analysis completed for {filename}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing photo {image_path}: {str(e)}")
            return {'error': str(e)}
    
    def suggest_pricing(self, photographer_profile: Dict, booking_details: Dict) -> Dict[str, Any]:
        """
        Generate intelligent pricing suggestions based on multiple factors
        """
        try:
            pricing_analysis = {
                'suggested_price': 0,
                'price_range': {'min': 0, 'max': 0},
                'factors_considered': [],
                'market_analysis': {},
                'recommendations': []
            }
            
            # Get base category pricing
            category = booking_details.get('category', 'portrait')
            base_price = self.pricing_factors['base_rates'].get(category, 500)
            
            # Apply experience multiplier
            experience_level = self._determine_experience_level(photographer_profile)
            experience_multiplier = self.pricing_factors['experience_multiplier'][experience_level]
            
            # Market demand analysis
            market_demand = self._analyze_market_demand(category, booking_details.get('date'))
            demand_multiplier = self.pricing_factors['market_factors'][market_demand]
            
            # Duration and complexity factors
            duration_hours = booking_details.get('duration', 4)
            duration_multiplier = 1 + (duration_hours - 4) * 0.1  # Base 4 hours
            
            # Location factor
            location_multiplier = self._get_location_multiplier(booking_details.get('location', ''))
            
            # Calculate suggested price
            suggested_price = base_price * experience_multiplier * demand_multiplier * duration_multiplier * location_multiplier
            
            # Create price range
            price_range_min = suggested_price * 0.8
            price_range_max = suggested_price * 1.2
            
            pricing_analysis.update({
                'suggested_price': round(suggested_price, 2),
                'price_range': {
                    'min': round(price_range_min, 2),
                    'max': round(price_range_max, 2)
                },
                'factors_considered': [
                    f"Base {category} rate: ${base_price}",
                    f"Experience level ({experience_level}): {experience_multiplier}x",
                    f"Market demand ({market_demand}): {demand_multiplier}x",
                    f"Duration ({duration_hours}h): {duration_multiplier:.1f}x",
                    f"Location factor: {location_multiplier:.1f}x"
                ],
                'market_analysis': {
                    'category_average': base_price,
                    'demand_level': market_demand,
                    'seasonal_factor': self._get_seasonal_factor(),
                    'competition_level': 'moderate'  # Could be enhanced with real data
                },
                'recommendations': self._generate_pricing_recommendations(suggested_price, photographer_profile)
            })
            
            logger.info(f"Pricing analysis completed for {category} booking")
            return pricing_analysis
            
        except Exception as e:
            logger.error(f"Error in pricing analysis: {str(e)}")
            return {'error': str(e)}
    
    def analyze_review_sentiment(self, review_text: str, rating: int = None) -> Dict[str, Any]:
        """
        Analyze sentiment of review text and provide insights
        """
        try:
            sentiment_analysis = {
                'sentiment': 'neutral',
                'confidence': 0.0,
                'key_phrases': [],
                'emotional_indicators': {},
                'suggestions': [],
                'rating_consistency': True
            }
            
            if not review_text:
                return sentiment_analysis
            
            review_lower = review_text.lower()
            words = re.findall(r'\b\w+\b', review_lower)
            
            # Sentiment scoring
            positive_score = sum(1 for word in words if word in self.sentiment_indicators['positive'])
            negative_score = sum(1 for word in words if word in self.sentiment_indicators['negative'])
            neutral_score = sum(1 for word in words if word in self.sentiment_indicators['neutral'])
            
            total_sentiment_words = positive_score + negative_score + neutral_score
            
            if total_sentiment_words > 0:
                if positive_score > negative_score and positive_score > neutral_score:
                    sentiment_analysis['sentiment'] = 'positive'
                    sentiment_analysis['confidence'] = positive_score / total_sentiment_words
                elif negative_score > positive_score and negative_score > neutral_score:
                    sentiment_analysis['sentiment'] = 'negative'
                    sentiment_analysis['confidence'] = negative_score / total_sentiment_words
                else:
                    sentiment_analysis['sentiment'] = 'neutral'
                    sentiment_analysis['confidence'] = max(neutral_score, positive_score, negative_score) / total_sentiment_words
            
            # Extract key phrases
            sentiment_analysis['key_phrases'] = self._extract_key_phrases(review_text)
            
            # Emotional indicators
            sentiment_analysis['emotional_indicators'] = {
                'enthusiasm': positive_score,
                'concerns': negative_score,
                'satisfaction': neutral_score + positive_score
            }
            
            # Check rating consistency
            if rating:
                expected_sentiment = 'positive' if rating >= 4 else 'negative' if rating <= 2 else 'neutral'
                sentiment_analysis['rating_consistency'] = sentiment_analysis['sentiment'] == expected_sentiment
            
            # Generate suggestions
            sentiment_analysis['suggestions'] = self._generate_review_suggestions(sentiment_analysis)
            
            logger.info(f"Sentiment analysis completed: {sentiment_analysis['sentiment']}")
            return sentiment_analysis
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return {'error': str(e)}
    
    def generate_ai_insights(self, photographer_id: int) -> Dict[str, Any]:
        """
        Generate comprehensive AI insights for photographer dashboard
        """
        try:
            # This would integrate with your models
            # For now, providing structure for implementation
            insights = {
                'performance_metrics': {
                    'booking_trends': {},
                    'revenue_optimization': {},
                    'client_satisfaction': {}
                },
                'recommendations': {
                    'pricing_adjustments': [],
                    'portfolio_improvements': [],
                    'marketing_suggestions': []
                },
                'predictions': {
                    'demand_forecast': {},
                    'revenue_projection': {},
                    'growth_opportunities': []
                },
                'competitive_analysis': {
                    'market_position': 'growing',
                    'strengths': [],
                    'improvement_areas': []
                }
            }
            
            # Placeholder insights - would be populated with real data
            insights['recommendations']['pricing_adjustments'] = [
                "Consider increasing wedding photography rates by 15% based on market demand",
                "Portrait session pricing is competitive - maintain current rates",
                "Offer package deals for corporate events to increase bookings"
            ]
            
            insights['recommendations']['portfolio_improvements'] = [
                "Add more diverse wedding shots to showcase range",
                "Include before/after editing examples",
                "Consider adding video testimonials from clients"
            ]
            
            logger.info(f"AI insights generated for photographer {photographer_id}")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {str(e)}")
            return {'error': str(e)}
    
    # Helper methods
    def _suggest_photo_editing(self, filename: str) -> List[str]:
        """Suggest editing improvements based on photo analysis"""
        suggestions = []
        
        if 'dark' in filename or 'night' in filename:
            suggestions.append("Consider brightening exposure")
        if 'portrait' in filename:
            suggestions.append("Apply skin smoothing if needed")
        if 'landscape' in filename:
            suggestions.append("Enhance colors and contrast")
        if 'wedding' in filename:
            suggestions.append("Apply warm color grading")
        
        return suggestions or ["Standard color correction recommended"]
    
    def _generate_seo_keywords(self, categories: List[str]) -> List[str]:
        """Generate SEO-friendly keywords"""
        base_keywords = ["photography", "photographer", "professional"]
        for category in categories:
            base_keywords.extend([
                f"{category} photography",
                f"{category} photographer",
                f"professional {category}"
            ])
        return base_keywords
    
    def _generate_photo_recommendations(self, analysis: Dict) -> List[str]:
        """Generate actionable recommendations for photos"""
        recommendations = []
        
        if analysis['categories']:
            primary_category = analysis['categories'][0]
            recommendations.append(f"Perfect for {primary_category} portfolio section")
            recommendations.append(f"Consider featuring in {primary_category} gallery")
        
        if len(analysis['suggested_tags']) > 5:
            recommendations.append("Rich content - great for SEO optimization")
        
        return recommendations
    
    def _determine_experience_level(self, profile: Dict) -> str:
        """Determine photographer experience level"""
        years_experience = profile.get('years_experience', 0)
        total_bookings = profile.get('total_bookings', 0)
        avg_rating = profile.get('average_rating', 0)
        
        if years_experience >= 5 and total_bookings >= 100 and avg_rating >= 4.5:
            return 'expert'
        elif years_experience >= 3 and total_bookings >= 50 and avg_rating >= 4.0:
            return 'advanced'
        elif years_experience >= 1 and total_bookings >= 10:
            return 'intermediate'
        else:
            return 'beginner'
    
    def _analyze_market_demand(self, category: str, booking_date: str = None) -> str:
        """Analyze market demand for specific category and date"""
        # Simulate market analysis
        high_demand_categories = ['wedding', 'commercial']
        
        if category in high_demand_categories:
            return 'high_demand'
        
        # Check seasonal factors if date provided
        if booking_date:
            try:
                date_obj = datetime.fromisoformat(booking_date.replace('Z', '+00:00'))
                if date_obj.month in [6, 7, 8, 12]:  # Peak wedding/holiday seasons
                    return 'high_demand'
            except:
                pass
        
        return 'normal_demand'
    
    def _get_location_multiplier(self, location: str) -> float:
        """Get pricing multiplier based on location"""
        premium_areas = ['downtown', 'city center', 'luxury', 'resort']
        
        location_lower = location.lower()
        if any(area in location_lower for area in premium_areas):
            return 1.2
        
        return 1.0
    
    def _get_seasonal_factor(self) -> float:
        """Get seasonal pricing factor"""
        current_month = datetime.now().month
        
        # Peak seasons: June-August (summer), December (holidays)
        if current_month in [6, 7, 8, 12]:
            return 1.2
        # Low season: January-March
        elif current_month in [1, 2, 3]:
            return 0.9
        
        return 1.0
    
    def _generate_pricing_recommendations(self, suggested_price: float, profile: Dict) -> List[str]:
        """Generate pricing strategy recommendations"""
        recommendations = []
        
        experience_level = self._determine_experience_level(profile)
        
        if experience_level == 'beginner':
            recommendations.append("Consider offering introductory packages to build portfolio")
            recommendations.append("Focus on building reviews before increasing rates")
        elif experience_level == 'expert':
            recommendations.append("You can command premium rates for specialized services")
            recommendations.append("Consider offering masterclass workshops as additional revenue")
        
        if suggested_price > 1000:
            recommendations.append("Consider offering payment plans for high-value bookings")
        
        return recommendations
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from review text"""
        # Simple phrase extraction
        positive_phrases = []
        negative_phrases = []
        
        sentences = text.split('.')
        for sentence in sentences:
            sentence = sentence.strip().lower()
            if any(word in sentence for word in self.sentiment_indicators['positive']):
                positive_phrases.append(sentence[:50] + "..." if len(sentence) > 50 else sentence)
            elif any(word in sentence for word in self.sentiment_indicators['negative']):
                negative_phrases.append(sentence[:50] + "..." if len(sentence) > 50 else sentence)
        
        return positive_phrases + negative_phrases
    
    def _generate_review_suggestions(self, analysis: Dict) -> List[str]:
        """Generate suggestions based on review sentiment"""
        suggestions = []
        
        if analysis['sentiment'] == 'positive':
            suggestions.append("Great feedback! Consider featuring this review prominently")
            suggestions.append("Ask this client for referrals")
        elif analysis['sentiment'] == 'negative':
            suggestions.append("Address concerns promptly and professionally")
            suggestions.append("Use feedback to improve service quality")
            suggestions.append("Consider reaching out to discuss resolution")
        else:
            suggestions.append("Encourage more detailed feedback from clients")
        
        if not analysis['rating_consistency']:
            suggestions.append("Review text sentiment doesn't match rating - follow up needed")
        
        return suggestions


# Initialize AI service instance
ai_service = PhotoRwAIService()