from django.core.management.base import BaseCommand
from payments.models import PaymentGateway, PlatformCommission
from decimal import Decimal


class Command(BaseCommand):
    help = 'Initialize payment gateways and commission settings'
    
    def handle(self, *args, **options):
        self.stdout.write('Setting up payment gateways...')
        
        # Create payment gateways
        gateways = [
            {
                'name': 'Stripe',
                'is_active': True,
                'supports_escrow': True,
                'processing_fee_percentage': Decimal('0.029'),  # 2.9%
                'fixed_fee': Decimal('0.30'),
                'currency': 'USD'
            },
            {
                'name': 'MTN Mobile Money',
                'is_active': True,
                'supports_escrow': False,
                'processing_fee_percentage': Decimal('0.015'),  # 1.5%
                'fixed_fee': Decimal('0.00'),
                'currency': 'RWF'
            },
            {
                'name': 'Airtel Money',
                'is_active': True,
                'supports_escrow': False,
                'processing_fee_percentage': Decimal('0.015'),  # 1.5%
                'fixed_fee': Decimal('0.00'),
                'currency': 'RWF'
            },
            {
                'name': 'PayPal',
                'is_active': True,
                'supports_escrow': True,
                'processing_fee_percentage': Decimal('0.034'),  # 3.4%
                'fixed_fee': Decimal('0.30'),
                'currency': 'USD'
            }
        ]
        
        for gateway_data in gateways:
            gateway, created = PaymentGateway.objects.get_or_create(
                name=gateway_data['name'],
                defaults=gateway_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created payment gateway: {gateway.name}')
                )
            else:
                self.stdout.write(f'Payment gateway already exists: {gateway.name}')
        
        # Create initial commission rate
        if not PlatformCommission.objects.filter(is_active=True).exists():
            commission = PlatformCommission.objects.create(
                commission_percentage=Decimal('10.00'),  # 10%
                is_active=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created initial commission rate: {commission.commission_percentage}%')
            )
        else:
            self.stdout.write('Commission rate already configured')
        
        self.stdout.write(self.style.SUCCESS('Payment system setup completed!'))