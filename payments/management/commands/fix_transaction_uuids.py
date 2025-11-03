import uuid
from django.core.management.base import BaseCommand
from django.db import connection
from payments.models import Transaction


class Command(BaseCommand):
    help = 'Fix invalid UUIDs in Transaction model'

    def handle(self, *args, **options):
        self.stdout.write('Fixing invalid UUIDs in transactions...')
        
        # Use raw SQL to update invalid UUIDs
        with connection.cursor() as cursor:
            # First, let's see what we're dealing with
            cursor.execute("SELECT id, transaction_id FROM payments_transaction WHERE transaction_id IS NOT NULL")
            transactions = cursor.fetchall()
            
            self.stdout.write(f'Found {len(transactions)} transactions to check...')
            
            fixed_count = 0
            for transaction_id, current_uuid in transactions:
                try:
                    # Try to create a UUID object to validate
                    uuid.UUID(current_uuid)
                except (ValueError, TypeError):
                    # Generate a new UUID for invalid ones
                    new_uuid = str(uuid.uuid4())
                    cursor.execute(
                        "UPDATE payments_transaction SET transaction_id = %s WHERE id = %s",
                        [new_uuid, transaction_id]
                    )
                    fixed_count += 1
                    self.stdout.write(f'Fixed transaction {transaction_id}: {current_uuid} -> {new_uuid}')
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully fixed {fixed_count} invalid UUIDs')
            )