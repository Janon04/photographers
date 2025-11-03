from django.core.management.base import BaseCommand
from django.utils import timezone
from payments.services import payment_service
from payments.models import PlatformRevenue


class Command(BaseCommand):
    help = 'Release funds from escrow and calculate daily revenue'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to wait before auto-releasing escrow (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be released without actually releasing'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting escrow release process (waiting {days} days)...')
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No actual changes will be made'))
            # Show what would be released
            cutoff_date = timezone.now() - timezone.timedelta(days=days)
            from payments.models import Transaction
            
            escrow_transactions = Transaction.objects.filter(
                status='held_escrow',
                created_at__lt=cutoff_date
            )
            
            if escrow_transactions.exists():
                self.stdout.write(f'Would release {escrow_transactions.count()} transactions:')
                for transaction in escrow_transactions:
                    self.stdout.write(
                        f'  - {transaction.transaction_id} ({transaction.amount} RWF) '
                        f'for {transaction.booking.photographer.get_full_name()}'
                    )
            else:
                self.stdout.write('No transactions ready for auto-release')
        else:
            # Actually release escrow
            released_count = payment_service.auto_release_escrow(days=days)
            
            if released_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully released {released_count} transactions from escrow')
                )
            else:
                self.stdout.write('No transactions were ready for auto-release')
        
        # Calculate daily revenue for yesterday
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        if not dry_run:
            revenue = PlatformRevenue.calculate_daily_revenue(yesterday)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Updated revenue for {yesterday}: {revenue.net_revenue} RWF '
                    f'({revenue.total_transactions} transactions)'
                )
            )
        
        self.stdout.write(self.style.SUCCESS('Escrow release process completed!'))