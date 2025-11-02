import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reviews.models import Review

reviews = Review.objects.all()
print(f'Total reviews: {reviews.count()}')

for r in reviews[:10]:
    print(f'Review {r.id}:')
    print(f'  - Reviewer: {r.reviewer}')
    print(f'  - Anonymous name: {r.anonymous_name}')
    print(f'  - Comment length: {len(r.comment) if r.comment else 0}')
    print(f'  - Comment preview: "{r.comment[:100] if r.comment else "EMPTY"}"')
    print(f'  - Overall rating: {r.overall_rating}')
    print(f'  - Approved: {r.is_approved}')
    print('---')