from django.db.models import Sum
from django.utils import timezone

def subscription_sidebar_stats(request):
    """
    Context processor to provide subscription statistics for the admin sidebar
    """
    # Only add subscription stats for admin dashboard pages
    if not request.path.startswith('/admin-dashboard/'):
        return {}
    
    try:
        from payments.models import UserSubscription, SubscriptionPayment
        
        # Get current subscription statistics
        total_subscriptions = UserSubscription.objects.count()
        active_subscriptions = UserSubscription.objects.filter(status='active').count()
        
        # Current month subscription revenue
        current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue = SubscriptionPayment.objects.filter(
            status='paid', 
            created_at__gte=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return {
            'subscription_stats': {
                'total_subscriptions': total_subscriptions,
                'active_subscriptions': active_subscriptions,
                'monthly_revenue': f"{monthly_revenue:.0f}",
            }
        }
    except ImportError:
        # If models are not available, return empty stats
        return {
            'subscription_stats': {
                'total_subscriptions': 0,
                'active_subscriptions': 0,
                'monthly_revenue': '0',
            }
        }