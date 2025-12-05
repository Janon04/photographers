from django.core.management.base import BaseCommand
from bookings.models import Booking
from django.utils import timezone

class Command(BaseCommand):
    help = 'Check booking dates and timestamps'

    def handle(self, *args, **options):
        bookings = Booking.objects.all().order_by('-created_at')
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"Total Bookings: {bookings.count()}")
        self.stdout.write(f"{'='*60}\n")
        
        for i, booking in enumerate(bookings, 1):
            self.stdout.write(f"\nBooking #{i}:")
            self.stdout.write(f"  ID: {booking.id}")
            self.stdout.write(f"  Created At: {booking.created_at}")
            self.stdout.write(f"  Service: {booking.get_service_type_display()}")
            self.stdout.write(f"  Status: {booking.status}")
            self.stdout.write(f"  Photographer: {booking.photographer.get_full_name()}")
            self.stdout.write(f"  Client: {booking.client.get_full_name() if booking.client else booking.client_name}")
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"Current Time (server): {timezone.now()}")
        self.stdout.write(f"{'='*60}\n")
