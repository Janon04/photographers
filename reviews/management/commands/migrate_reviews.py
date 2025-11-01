"""
Management command to migrate existing reviews to new enhanced model
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db import models
from reviews.models import Review


class Command(BaseCommand):
    help = 'Migrate existing reviews to enhanced model structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write('Starting review migration...')
        
        reviews_to_update = Review.objects.filter(
            models.Q(overall_rating__isnull=True) |
            models.Q(quality_rating__isnull=True) |
            models.Q(title__isnull=True) |
            models.Q(title='')
        )
        
        total_reviews = reviews_to_update.count()
        self.stdout.write(f'Found {total_reviews} reviews to migrate')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))
            for review in reviews_to_update[:10]:  # Show first 10
                self.stdout.write(f'Would update: Review {review.id} by {review.reviewer}')
            return
        
        updated_count = 0
        
        with transaction.atomic():
            for review in reviews_to_update:
                # Migrate legacy rating field to new structure
                if not review.overall_rating and review.rating:
                    review.overall_rating = review.rating
                
                # Set default detailed ratings if not set
                if not review.quality_rating:
                    review.quality_rating = review.overall_rating or review.rating or 5
                if not review.professionalism_rating:
                    review.professionalism_rating = review.overall_rating or review.rating or 5
                if not review.communication_rating:
                    review.communication_rating = review.overall_rating or review.rating or 5
                if not review.value_rating:
                    review.value_rating = review.overall_rating or review.rating or 5
                
                # Generate title if missing
                if not review.title:
                    rating = review.overall_rating or review.rating
                    if rating >= 4:
                        review.title = "Great experience!"
                    elif rating >= 3:
                        review.title = "Good service"
                    else:
                        review.title = "Room for improvement"
                
                # Set default verification status
                if review.is_verified is None:
                    review.is_verified = True
                
                try:
                    review.save()
                    updated_count += 1
                    
                    if updated_count % 10 == 0:
                        self.stdout.write(f'Updated {updated_count} reviews...')
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error updating review {review.id}: {str(e)}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully migrated {updated_count} reviews')
        )
        
        # Run sentiment analysis on reviews that don't have it
        self.stdout.write('Running sentiment analysis on migrated reviews...')
        
        reviews_for_analysis = Review.objects.filter(
            analysis_status='pending'
        )[:50]  # Limit to avoid timeout
        
        analysis_count = 0
        for review in reviews_for_analysis:
            try:
                review.analyze_sentiment()
                analysis_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Sentiment analysis failed for review {review.id}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Completed sentiment analysis for {analysis_count} reviews')
        )