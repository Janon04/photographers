#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User

total_users = User.objects.count()
clients = User.objects.filter(role='client').count()
photographers = User.objects.filter(role='photographer').count()

print(f"Total users: {total_users}")
print(f"Clients: {clients}")
print(f"Photographers: {photographers}")

if total_users > 0:
    print("\nFirst few users:")
    for user in User.objects.all()[:5]:
        print(f"- {user.username} ({user.role})")