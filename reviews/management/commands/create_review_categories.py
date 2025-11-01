"""
Management command to create initial review categories
"""
from django.core.management.base import BaseCommand
from reviews.models import ReviewCategory


class Command(BaseCommand):
    help = 'Create initial review categories'

    def handle(self, *args, **options):
        categories = [
            {
                'name': 'Wedding Photography',
                'description': 'Reviews related to wedding photography services'
            },
            {
                'name': 'Portrait Photography',
                'description': 'Reviews for portrait and headshot sessions'
            },
            {
                'name': 'Event Photography',
                'description': 'Reviews for corporate events and special occasions'
            },
            {
                'name': 'Family Photography',
                'description': 'Reviews for family photo sessions'
            },
            {
                'name': 'Newborn Photography',
                'description': 'Reviews for newborn and baby photography'
            },
            {
                'name': 'Engagement Photography',
                'description': 'Reviews for engagement photo sessions'
            },
            {
                'name': 'Commercial Photography',
                'description': 'Reviews for business and commercial photography'
            },
            {
                'name': 'Fashion Photography',
                'description': 'Reviews for fashion and modeling shoots'
            },
            {
                'name': 'Product Photography',
                'description': 'Reviews for product and e-commerce photography'
            },
            {
                'name': 'Real Estate Photography',
                'description': 'Reviews for property and real estate photography'
            }
        ]

        created_count = 0
        for category_data in categories:
            category, created = ReviewCategory.objects.get_or_create(
                name=category_data['name'],
                defaults={'description': category_data['description']}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new categories.')
        )