from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a platform admin user'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Admin email', required=True)
        parser.add_argument('--password', type=str, help='Admin password', required=True)
        parser.add_argument('--first-name', type=str, help='First name', default='Platform')
        parser.add_argument('--last-name', type=str, help='Last name', default='Admin')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        
        # Check if admin user already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'Admin user with email {email} already exists.')
            )
            return
        
        # Create admin user
        admin_user = User.objects.create_user(
            email=email,
            username=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=User.Roles.ADMIN,
            is_verified=True,
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created admin user: {email}')
        )