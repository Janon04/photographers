"""
Management command to ensure Site object exists for Django Sites framework
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = 'Ensure Site object exists for Django Sites framework'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            default='127.0.0.1:8000',
            help='Domain for the site (default: 127.0.0.1:8000)',
        )
        parser.add_argument(
            '--name',
            type=str,
            default='PhotoRw',
            help='Name for the site (default: PhotoRw)',
        )

    def handle(self, *args, **options):
        site_id = getattr(settings, 'SITE_ID', 1)
        domain = options['domain']
        name = options['name']
        
        self.stdout.write(f"Checking Site object with ID: {site_id}")
        
        try:
            site = Site.objects.get(pk=site_id)
            self.stdout.write(f"Site exists: {site.domain} - {site.name}")
            
            # Update if different
            if site.domain != domain or site.name != name:
                site.domain = domain
                site.name = name
                site.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Updated site: {domain} - {name}")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("Site is already correctly configured")
                )
                
        except Site.DoesNotExist:
            site = Site.objects.create(
                pk=site_id,
                domain=domain,
                name=name
            )
            self.stdout.write(
                self.style.SUCCESS(f"Created site: {domain} - {name}")
            )
        
        self.stdout.write(
            self.style.SUCCESS(f"Site framework is ready! (ID: {site.id})")
        )