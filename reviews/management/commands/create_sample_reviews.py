from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from reviews.models import Review, ReviewCategory
from bookings.models import Booking
from users.models import User
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Creates sample reviews for testing'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Sample review data
        sample_reviews = [
            {
                'title': 'Outstanding Wedding Photography',
                'comment': 'The photographer captured every special moment perfectly. Professional, creative, and delivered exactly what we wanted for our wedding day.',
                'overall_rating': 5,
                'quality_rating': 5,
                'professionalism_rating': 5,
                'communication_rating': 4,
                'value_rating': 4
            },
            {
                'title': 'Great Portrait Session',
                'comment': 'Amazing experience for our family portraits. The photographer was patient with our kids and made everyone feel comfortable.',
                'overall_rating': 4,
                'quality_rating': 5,
                'professionalism_rating': 4,
                'communication_rating': 5,
                'value_rating': 4
            },
            {
                'title': 'Professional Event Coverage',
                'comment': 'Excellent coverage of our corporate event. Captured all the important moments and delivered high-quality photos promptly.',
                'overall_rating': 5,
                'quality_rating': 5,
                'professionalism_rating': 5,
                'communication_rating': 5,
                'value_rating': 3
            },
            {
                'title': 'Beautiful Landscape Photos',
                'comment': 'Stunning work capturing the beauty of Rwanda\'s landscapes. Highly recommend for any outdoor photography needs.',
                'overall_rating': 4,
                'quality_rating': 5,
                'professionalism_rating': 4,
                'communication_rating': 4,
                'value_rating': 4
            },
            {
                'title': 'Creative and Artistic',
                'comment': 'The photographer brought a unique artistic vision to our photo shoot. Very creative approach and excellent results.',
                'overall_rating': 5,
                'quality_rating': 5,
                'professionalism_rating': 4,
                'communication_rating': 4,
                'value_rating': 5
            },
            {
                'title': 'Perfect Product Photography',
                'comment': 'Exactly what we needed for our business catalog. Clean, professional shots that showcase our products beautifully.',
                'overall_rating': 4,
                'quality_rating': 4,
                'professionalism_rating': 5,
                'communication_rating': 4,
                'value_rating': 4
            }
        ]
        
        # Get some users to be reviewers and photographers
        clients = User.objects.filter(role='client')[:10]
        photographers = User.objects.filter(role='photographer')[:5]
        
        if not clients.exists() or not photographers.exists():
            self.stdout.write(
                self.style.WARNING('Need at least 1 client and 1 photographer to create sample reviews')
            )
            return
        
        # Create sample categories if they don't exist
        categories = ['Wedding', 'Portrait', 'Event', 'Landscape', 'Product', 'Fashion']
        for cat_name in categories:
            ReviewCategory.objects.get_or_create(
                name=cat_name,
                defaults={'description': f'{cat_name} photography reviews', 'is_active': True}
            )
        
        review_categories = list(ReviewCategory.objects.filter(is_active=True))
        
        created_count = 0
        
        for i, review_data in enumerate(sample_reviews):
            try:
                # Pick random client and photographer
                reviewer = random.choice(clients)
                photographer = random.choice(photographers)
                
                # Skip if this combination already has a review
                if Review.objects.filter(reviewer=reviewer, photographer=photographer).exists():
                    continue
                
                # Create a booking for this review (simplified)
                booking, created = Booking.objects.get_or_create(
                    client=reviewer,
                    photographer=photographer,
                    defaults={
                        'event_type': random.choice(['wedding', 'portrait', 'event', 'product']),
                        'event_date': datetime.now() + timedelta(days=random.randint(1, 30)),
                        'status': 'completed',
                        'total_amount': random.randint(100, 1000)
                    }
                )
                
                # Create the review
                review = Review.objects.create(
                    reviewer=reviewer,
                    photographer=photographer,
                    booking=booking,
                    title=review_data['title'],
                    comment=review_data['comment'],
                    overall_rating=review_data['overall_rating'],
                    quality_rating=review_data['quality_rating'],
                    professionalism_rating=review_data['professionalism_rating'],
                    communication_rating=review_data['communication_rating'],
                    value_rating=review_data['value_rating'],
                    is_approved=True
                )
                
                # Add random categories
                selected_categories = random.sample(review_categories, random.randint(1, 3))
                review.categories.set(selected_categories)
                
                created_count += 1
                self.stdout.write(f'Created review: {review.title}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating review {i}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample reviews')
        )