from django.core.management.base import BaseCommand
from users.models import User

class Command(BaseCommand):
    help = 'Fix users with empty email addresses by setting a placeholder.'

    def handle(self, *args, **options):
        users = User.objects.filter(email='')
        count = 0
        for user in users:
            user.email = f'fixme_{user.pk}@example.com'
            user.save()
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Fixed {count} users with empty emails.'))
