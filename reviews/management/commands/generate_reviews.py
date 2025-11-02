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
        
        # Get or create clients with authentic Rwandan names
        rwanda_client_names = [
            ('Uwimana', 'Grace', 'grace.uwimana'),
            ('Nshuti', 'David', 'david.nshuti'), 
            ('Mukamana', 'Alice', 'alice.mukamana'),
            ('Habimana', 'Jean-Claude', 'jean.habimana'),
            ('Nyirahabimana', 'Marie', 'marie.nyirahabimana')
        ]
        
        clients = list(User.objects.filter(role='client'))
        if len(clients) < 3:
            # Create sample clients with Rwandan names
            for i, (last_name, first_name, username) in enumerate(rwanda_client_names[:3]):
                if not User.objects.filter(username=username).exists():
                    client = User.objects.create_user(
                        username=username,
                        email=f'{username}@gmail.com',
                        password='testpass123',
                        first_name=first_name,
                        last_name=last_name,
                        role='client'
                    )
                    clients.append(client)
                    self.stdout.write(f'Created client: {client.get_full_name()} ({client.username})')
        
        photographers = list(User.objects.filter(role='photographer'))
        
        if len(clients) < 1 or len(photographers) < 1:
            self.stdout.write(
                self.style.ERROR('Need at least 1 client and 1 photographer to create sample reviews')
            )
            return

        # Realistic review texts for Rwanda photography services
        positive_reviews = [
            "Absolutely amazing photographer! Captured our traditional Rwandan wedding ceremony beautifully at Serena Hotel. Every cultural detail was preserved perfectly.",
            "Professional service from start to finish. The photos from our engagement at Kigali Golf Club exceeded all expectations! Highly recommend.",
            "Incredible attention to detail during our corporate event at Kigali Convention Centre. The photographer understood our business needs perfectly.",
            "Outstanding maternity photography session in Nyarutarama. The natural lighting and scenic backdrop made for stunning photos we'll treasure forever.",
            "Perfect family portrait session! The photographer was patient with our children and captured beautiful moments at Lake Kivu. Simply the best!",
            "Exceptional wedding photography at Volcanoes National Park. The mountain backdrop and professional service made our special day unforgettable.",
            "Great cultural event photography at our traditional ceremony in Nyanza. The photographer respected our customs and delivered beautiful results.",
        ]
        
        neutral_reviews = [
            "Good photography service for our event in Kimihurura. Photos were delivered on time and met our expectations.",
            "Professional photographer with decent results at our corporate function in Remera. Some photos were excellent, others were standard quality.",
            "Reliable service for our graduation ceremony in Butare. The photographer was punctual and delivered as promised.",
            "Satisfied with the wedding photography at Hotel des Mille Collines. Good value for money and professional approach.",
        ]
        
        negative_reviews = [
            "Photos from our event in Muhanga were delivered late and some important cultural moments were missed. Expected better quality.",
            "Communication could have been improved. Some key shots from our ceremony in Gisenyi were not captured as discussed.",
            "The photographer seemed unfamiliar with traditional Rwandan ceremonies. Some cultural aspects were not captured appropriately.",
        ]

        # Real Rwanda locations for bookings
        rwanda_locations = [
            'Kigali Convention Centre, Gasabo, Kigali',
            'Hotel des Mille Collines, Nyarugenge, Kigali',
            'Serena Hotel Kigali, Kiyovu, Kigali',
            'Lake Kivu Serena Hotel, Gisenyi, Rubavu',
            'Akagera National Park, Kayonza',
            'Volcanoes National Park, Musanze',
            'Nyungwe Forest National Park, Nyamagabe',
            'King Faisal Hospital, Kacyiru, Kigali',
            'Kigali Golf Club, Nyarutarama, Kigali',
            'Gishushu, Gasabo, Kigali',
            'Kimihurura, Gasabo, Kigali',
            'Remera, Gasabo, Kigali',
            'Nyamirambo, Nyarugenge, Kigali',
            'Kibuye, Karongi',
            'Butare, Huye',
            'Ruhengeri, Musanze',
            'Gisenyi Beach, Rubavu',
            'Muhanga Town, Muhanga',
            'Nyanza Palace, Nyanza',
            'Hotel Gorillas, Musanze'
        ]

        # Realistic service types for Rwanda
        service_types = [
            'wedding', 'engagement', 'portrait', 'maternity', 'newborn',
            'corporate', 'event', 'cultural', 'graduation', 'anniversary'
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
                    service_type=random.choice(service_types),
                    location=random.choice(rwanda_locations),
                    status='completed'
                )
                existing_bookings.append(booking)
                self.stdout.write(f'Created booking: {client.username} -> {photographer.username} at {booking.location}')

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
                is_approved=True,  # Auto-approve sample reviews
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