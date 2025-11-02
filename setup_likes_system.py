import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reviews.models import Review, ReviewLikeStats
from users.models import User

print("Setting up like/dislike statistics for existing reviews...")

# Get all reviews and create stats
reviews = Review.objects.filter(is_approved=True)
print(f"Found {reviews.count()} approved reviews")

for review in reviews:
    stats, created = ReviewLikeStats.objects.get_or_create(review=review)
    if created:
        print(f"Created stats for review {review.id}")
    stats.update_stats()

print("✅ Like/dislike system setup complete!")
print("\n📊 System Features:")
print("- 👍 Like/Dislike buttons on each review")
print("- 💬 Comment system with replies")
print("- 📈 Real-time statistics tracking")
print("- 🔒 Secure AJAX endpoints")
print("- 📱 Responsive design")
print("\n🎯 How to use:")
print("1. Visit /reviews/all/ to see reviews")
print("2. Login as any user to like/dislike reviews")
print("3. Click comment button to add comments")
print("4. Check admin panel for statistics")