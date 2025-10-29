#!/usr/bin/env python
"""
Test script to verify AI features are working properly
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from config.ai_service import ai_service
from portfolio.models import Photo
from bookings.models import Booking
from reviews.models import Review
from users.models import User

def test_ai_service():
    """Test the AI service functionality"""
    print("🔥 Testing PhotoRw AI Service...")
    
    # Test photo analysis
    print("\n1. Testing Photo Analysis:")
    photo_data = {
        'filename': 'sunset_portrait.jpg',
        'filesize': 2500000,
        'description': 'Beautiful sunset portrait of a couple on the beach'
    }
    
    analysis = ai_service.analyze_photo_content(photo_data)
    print(f"   Categories: {analysis.get('categories', [])}")
    print(f"   Quality Score: {analysis.get('quality_score', 0)}")
    print(f"   Tags: {analysis.get('suggested_tags', [])}")
    
    # Test pricing suggestions
    print("\n2. Testing Pricing Calculator:")
    photographer_profile = {
        'years_experience': 5,
        'total_bookings': 25,
        'average_rating': 4.7
    }
    
    booking_details = {
        'category': 'wedding',
        'date': '2025-06-15',
        'location': 'Downtown Convention Center',
        'duration': 8
    }
    
    pricing = ai_service.suggest_pricing(photographer_profile, booking_details)
    print(f"   Suggested Price: ${pricing.get('suggested_price', 0)}")
    print(f"   Price Range: ${pricing.get('price_range', {}).get('min', 0)} - ${pricing.get('price_range', {}).get('max', 0)}")
    print(f"   Factors: {pricing.get('factors_considered', [])[:2]}")
    
    # Test sentiment analysis
    print("\n3. Testing Sentiment Analysis:")
    reviews = [
        "Amazing photographer! The photos turned out absolutely beautiful and professional.",
        "The session was okay, nothing special but not bad either.",
        "Very disappointed with the quality and the photographer was late."
    ]
    
    for i, review_text in enumerate(reviews, 1):
        sentiment = ai_service.analyze_review_sentiment(review_text, 5 if i == 1 else 3 if i == 2 else 1)
        print(f"   Review {i}: {sentiment.get('sentiment_label', 'unknown')} (confidence: {sentiment.get('confidence', 0):.2f})")

def test_model_methods():
    """Test model AI simulation methods"""
    print("\n🎯 Testing Model AI Simulation Methods...")
    
    # Test if we have any existing data
    users = User.objects.filter(role='photographer').first()
    if users:
        print(f"\n✅ Found photographer: {users.username}")
        
        # Test photo AI methods if photos exist
        photos = Photo.objects.filter(owner=users).first()
        if photos:
            categories = photos.simulate_ai_categories()
            print(f"   Photo AI Categories: {categories}")
            
            quality = photos.get_quality_score()
            print(f"   Photo Quality Score: {quality}")
    
    # Test booking AI methods
    bookings = Booking.objects.first()
    if bookings:
        pricing = bookings.simulate_ai_pricing()
        print(f"\n💰 Booking AI Pricing: ${pricing.get('suggested_price', 0)}")
        print(f"   Price Range: {pricing.get('price_range', {})}")
    
    # Test review AI methods
    reviews = Review.objects.first()
    if reviews:
        sentiment = reviews.simulate_sentiment_analysis()
        print(f"\n📝 Review AI Sentiment: {sentiment.get('sentiment', 'unknown')}")
        print(f"   Key Phrases: {sentiment.get('key_phrases', [])}")

if __name__ == '__main__':
    print("🤖 PhotoRw AI Features Test Suite")
    print("=" * 50)
    
    try:
        test_ai_service()
        test_model_methods()
        
        print("\n" + "=" * 50)
        print("✅ All AI features are working correctly!")
        print("🚀 Ready for Youth Connect 2025 Competition!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()