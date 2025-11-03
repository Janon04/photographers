from django.core.management.base import BaseCommand
from payments.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Initialize subscription plans with the business model data'

    def handle(self, *args, **options):
        self.stdout.write("Creating subscription plans...")
        
        # Basic Plan
        basic_plan, created = SubscriptionPlan.objects.get_or_create(
            name='basic',
            defaults={
                'display_name': 'Basic Plan',
                'price_monthly': 2000,
                'price_yearly': 20000,  # 2 months free
                'currency': 'RWF',
                'features_description': '''Limited features
Basic support
No customization''',
                'support_level': 'Basic support',
                'customization_level': 'No customization',
                'max_photos_upload': 50,  # 50 photos per month
                'max_storage_gb': 5,  # 5GB storage
                'max_bookings_per_month': 10,  # 10 bookings per month
                'max_portfolio_items': 20,  # 20 portfolio items
                'additional_services': 'No additional services included',
                'includes_premium_support': False,
                'includes_consulting': False,
                'includes_add_ons': False,
                'commission_rate': 15.00,  # Higher commission for basic plan
                'priority_support': False,
                'analytics_access': False,
                'api_access': False,
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created Basic Plan - {basic_plan.price_monthly} RWF/month')
            )
        else:
            self.stdout.write(f'→ Basic Plan already exists')
            
        # Standard Plan
        standard_plan, created = SubscriptionPlan.objects.get_or_create(
            name='standard',
            defaults={
                'display_name': 'Standard Plan',
                'price_monthly': 15000,
                'price_yearly': 150000,  # 2 months free
                'currency': 'RWF',
                'features_description': '''More features
Standard support
Some customization''',
                'support_level': 'Standard support',
                'customization_level': 'Some customization',
                'max_photos_upload': 200,  # 200 photos per month
                'max_storage_gb': 25,  # 25GB storage
                'max_bookings_per_month': 50,  # 50 bookings per month
                'max_portfolio_items': 100,  # 100 portfolio items
                'additional_services': 'Optional add-ons available for purchase',
                'includes_premium_support': False,
                'includes_consulting': False,
                'includes_add_ons': True,
                'commission_rate': 10.00,  # Standard commission
                'priority_support': False,
                'analytics_access': True,
                'api_access': False,
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created Standard Plan - {standard_plan.price_monthly} RWF/month')
            )
        else:
            self.stdout.write(f'→ Standard Plan already exists')
            
        # Premium Plan
        premium_plan, created = SubscriptionPlan.objects.get_or_create(
            name='premium',
            defaults={
                'display_name': 'Premium Plan',
                'price_monthly': 35000,
                'price_yearly': 350000,  # 2 months free
                'currency': 'RWF',
                'features_description': '''Full features
Priority support
Full customization''',
                'support_level': 'Priority support',
                'customization_level': 'Full customization',
                'max_photos_upload': -1,  # Unlimited photos
                'max_storage_gb': -1,  # Unlimited storage
                'max_bookings_per_month': -1,  # Unlimited bookings
                'max_portfolio_items': -1,  # Unlimited portfolio items
                'additional_services': 'Premium support and consulting included',
                'includes_premium_support': True,
                'includes_consulting': True,
                'includes_add_ons': True,
                'commission_rate': 5.00,  # Lower commission for premium
                'priority_support': True,
                'analytics_access': True,
                'api_access': True,
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created Premium Plan - {premium_plan.price_monthly} RWF/month')
            )
        else:
            self.stdout.write(f'→ Premium Plan already exists')
            
        self.stdout.write(
            self.style.SUCCESS('\n🎉 Subscription plans initialization completed!')
        )
        
        # Display summary
        self.stdout.write('\n📊 Plan Summary:')
        for plan in SubscriptionPlan.objects.filter(is_active=True).order_by('price_monthly'):
            self.stdout.write(f'   • {plan.display_name}: {plan.price_monthly:,} RWF/month')
            self.stdout.write(f'     Commission: {plan.commission_rate}%')
            storage = f'{plan.max_storage_gb}GB' if plan.max_storage_gb != -1 else 'Unlimited'
            photos = f'{plan.max_photos_upload}' if plan.max_photos_upload != -1 else 'Unlimited'
            self.stdout.write(f'     Storage: {storage}, Photos: {photos}/month')
            self.stdout.write('')