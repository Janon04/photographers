from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from users.models import User
from bookings.models import Booking
from payments.models import Transaction


class Command(BaseCommand):
    help = 'Fix naive datetime fields by converting them to timezone-aware'

    def handle(self, *args, **options):
        # Fix Users with naive date_joined
        naive_users = User.objects.filter(date_joined__isnull=False)
        updated_users = 0
        
        for user in naive_users:
            if timezone.is_naive(user.date_joined):
                # Convert naive datetime to timezone-aware using Django's timezone utilities
                aware_datetime = timezone.make_aware(user.date_joined)
                user.date_joined = aware_datetime
                user.save(update_fields=['date_joined'])
                updated_users += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Fixed {updated_users} users with naive date_joined')
        )
        
        # Fix Bookings with naive created_at
        naive_bookings = Booking.objects.filter(created_at__isnull=False)
        updated_bookings = 0
        
        for booking in naive_bookings:
            if timezone.is_naive(booking.created_at):
                aware_datetime = timezone.make_aware(booking.created_at)
                booking.created_at = aware_datetime
                booking.save(update_fields=['created_at'])
                updated_bookings += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Fixed {updated_bookings} bookings with naive created_at')
        )
        
        # Fix Transactions with naive created_at
        try:
            naive_transactions = Transaction.objects.filter(created_at__isnull=False)
            updated_transactions = 0
            
            for transaction in naive_transactions:
                if timezone.is_naive(transaction.created_at):
                    aware_datetime = timezone.make_aware(transaction.created_at)
                    transaction.created_at = aware_datetime
                    transaction.save(update_fields=['created_at'])
                    updated_transactions += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Fixed {updated_transactions} transactions with naive created_at')
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not fix transactions: {e}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully completed timezone fix!')
        )