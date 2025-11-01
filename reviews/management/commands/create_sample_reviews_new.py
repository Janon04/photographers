import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from datetime import timedelta
from reviews.models import Review
from bookings.models import Booking


class Command(BaseCommand):
    help = 'Creates sample review data for testing'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Get or create clients
        clients = list(User.objects.filter(role='client'))
        if len(clients) < 3:
            # Create sample clients
            for i in range(3):
                client = User.objects.create_user(
                    username=f'client{i+1}',
                    email=f'client{i+1}@example.com',
                    password='testpass123',
                    first_name=f'Client{i+1}',
                    last_name='User',
                    role='client'
                )
                clients.append(client)
                self.stdout.write(f'Created client: {client.username}')
        
        photographers = list(User.objects.filter(role='photographer'))
        
        if len(clients) < 1 or len(photographers) < 1:
            self.stdout.write(
                self.style.ERROR('Need at least 1 client and 1 photographer to create sample reviews')
            )
            return

        # Sample review texts
        positive_reviews = [
            "Absolutely amazing photographer! The photos came out stunning and captured every special moment perfectly.",
            "Professional, creative, and so easy to work with. Our wedding photos exceeded all expectations!",
            "Incredible attention to detail and artistic vision. Would definitely recommend to anyone!",
            "Outstanding service from start to finish. The photographer was punctual, prepared, and delivered beautiful results.",
            "Simply the best! These photos will be treasured for a lifetime. Thank you for capturing our special day!",
        ]
        
        neutral_reviews = [
            "Good photographer with decent results. Photos were delivered on time as promised.",
            "Professional service overall. Some photos were great, others were just okay.",
            "Met expectations. The photographer was reliable and the photos turned out well.",
        ]
        
        negative_reviews = [
            "Photos were delivered late and some were out of focus. Expected better quality for the price.",
            "Communication could have been better. Some important shots were missed during the event.",
        ]

        # Create sample bookings first
        existing_bookings = []
        for client in clients:
            for photographer in photographers:
                # Create at least one booking between each client-photographer pair
                booking = Booking.objects.create(
                    client=client,
                    photographer=photographer,
                    date=timezone.now().date() - timedelta(days=random.randint(30, 180)),
                    time=timezone.now().time(),
                    service_type='wedding',
                    location='Sample Location',
                    status='completed'
                )
                existing_bookings.append(booking)
                self.stdout.write(f'Created booking: {client.username} -> {photographer.username}')

        # Create sample reviews
        created_count = 0
        for i in range(min(15, len(existing_bookings))):  # Create reviews for available bookings
            booking = existing_bookings[i % len(existing_bookings)]
            client = booking.client
            photographer = booking.photographer
            
            # Determine review sentiment
            sentiment_roll = random.random()
            if sentiment_roll < 0.7:  # 70% positive
                overall_rating = random.randint(4, 5)
                comment = random.choice(positive_reviews)
                sentiment = 'positive'
            elif sentiment_roll < 0.9:  # 20% neutral
                overall_rating = 3
                comment = random.choice(neutral_reviews)
                sentiment = 'neutral'
            else:  # 10% negative
                overall_rating = random.randint(1, 2)
                comment = random.choice(negative_reviews)
                sentiment = 'negative'
            
            # Create varied sub-ratings around the overall rating
            base_rating = overall_rating
            quality_rating = max(1, min(5, base_rating + random.randint(-1, 1)))
            professionalism_rating = max(1, min(5, base_rating + random.randint(-1, 1)))
            communication_rating = max(1, min(5, base_rating + random.randint(-1, 1)))
            value_rating = max(1, min(5, base_rating + random.randint(-1, 1)))
            
            # Random date in the last 6 months
            days_ago = random.randint(1, 180)
            created_date = timezone.now() - timedelta(days=days_ago)
            
            review = Review.objects.create(
                reviewer=client,
                photographer=photographer,
                booking=booking,
                overall_rating=overall_rating,
                quality_rating=quality_rating,
                professionalism_rating=professionalism_rating,
                communication_rating=communication_rating,
                value_rating=value_rating,
                comment=comment,
                created_at=created_date,
                updated_at=created_date
            )
            
            created_count += 1
            
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample reviews!')
        )
        
        # Show summary
        total_reviews = Review.objects.count()
        avg_rating = Review.objects.aggregate(
            avg=models.Avg('overall_rating')
        )['avg'] or 0
        
        self.stdout.write(f'Total reviews in database: {total_reviews}')
        self.stdout.write(f'Average rating: {avg_rating:.2f}')