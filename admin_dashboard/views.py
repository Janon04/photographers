from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
import csv

# Import models
from django.contrib.auth import get_user_model
from bookings.models import Booking
from payments.models import Transaction
from reviews.models import Review
from portfolio.models import Photo, ContactMessage
from community.models import Post
from blog.models import BlogPost
from .models import AdminActivityLog, PlatformSettings, SystemNotification, PlatformAnalytics
from .forms import UserEditForm, SystemNotificationForm, PlatformSettingsForm
from .email_service import NotificationEmailService

User = get_user_model()

def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and user.role == User.Roles.ADMIN

def parse_filter_date(date_str):
    """
    Helper function to properly parse date string and handle timezone conversion
    """
    if not date_str:
        return None
    
    try:
        # Parse the date string
        filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        return filter_date
    except ValueError:
        return None

def get_date_range_for_filter(filter_date):
    """
    Helper function to get timezone-aware datetime range for a given date
    """
    if not filter_date:
        return None, None
    
    # Create start and end datetime for the date using timezone.make_aware
    start_datetime = timezone.make_aware(
        datetime.combine(filter_date, datetime.min.time())
    )
    end_datetime = timezone.make_aware(
        datetime.combine(filter_date, datetime.max.time())
    )
    
    return start_datetime, end_datetime

def log_admin_activity(admin_user, action, target_model, target_id, target_description, details="", ip_address=None):
    """Log admin activity for audit trail"""
    AdminActivityLog.objects.create(
        admin_user=admin_user,
        action=action,
        target_model=target_model,
        target_id=target_id,
        target_description=target_description,
        details=details,
        ip_address=ip_address
    )

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Main admin dashboard with overview stats"""
    # Get filter date from request, default to today
    filter_date_str = request.GET.get('filter_date', '')
    filter_date = parse_filter_date(filter_date_str)
    
    if not filter_date:
        filter_date = timezone.now().date()
    
    # Get current date for analytics
    today = timezone.now().date()
    
    # Basic stats (filtered by date if provided)
    if filter_date_str:
        # Get timezone-aware datetime range for the filter date
        start_datetime, end_datetime = get_date_range_for_filter(filter_date)
        
        # Filter by specific date
        total_users = User.objects.filter(date_joined__lte=end_datetime).count()
        total_photographers = User.objects.filter(
            role=User.Roles.PHOTOGRAPHER, 
            date_joined__lte=end_datetime
        ).count()
        total_clients = User.objects.filter(
            role=User.Roles.CLIENT, 
            date_joined__lte=end_datetime
        ).count()
        total_bookings = Booking.objects.filter(created_at__lte=end_datetime).count()
        completed_bookings = Booking.objects.filter(
            status='completed', 
            created_at__lte=end_datetime
        ).count()
        pending_bookings = Booking.objects.filter(
            status='pending', 
            created_at__lte=end_datetime
        ).count()
        
        # Revenue stats for specific date
        total_revenue = Transaction.objects.filter(
            status='paid', 
            created_at__lte=end_datetime
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Activity for the specific date (range from start to end of day)
        new_users_30d = User.objects.filter(
            date_joined__gte=start_datetime, 
            date_joined__lte=end_datetime
        ).count()
        new_bookings_30d = Booking.objects.filter(
            created_at__gte=start_datetime, 
            created_at__lte=end_datetime
        ).count()
        
        # Recent activities for the specific date
        recent_users = User.objects.filter(
            date_joined__gte=start_datetime, 
            date_joined__lte=end_datetime
        ).order_by('-date_joined')[:5]
        recent_bookings = Booking.objects.filter(
            created_at__gte=start_datetime, 
            created_at__lte=end_datetime
        ).order_by('-created_at')[:5]
        recent_reviews = Review.objects.filter(
            created_at__gte=start_datetime, 
            created_at__lte=end_datetime
        ).order_by('-created_at')[:5]
        
    else:
        # Default behavior - all time stats
        total_users = User.objects.count()
        total_photographers = User.objects.filter(role=User.Roles.PHOTOGRAPHER).count()
        total_clients = User.objects.filter(role=User.Roles.CLIENT).count()
        total_bookings = Booking.objects.count()
        completed_bookings = Booking.objects.filter(status='completed').count()
        pending_bookings = Booking.objects.filter(status='pending').count()
        
        # Revenue stats
        total_revenue = Transaction.objects.filter(status='paid').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Recent activity stats
        last_30_days = timezone.now() - timedelta(days=30)
        new_users_30d = User.objects.filter(date_joined__gte=last_30_days).count()
        new_bookings_30d = Booking.objects.filter(created_at__gte=last_30_days).count()
        
        # Recent activities
        recent_users = User.objects.order_by('-date_joined')[:5]
        recent_bookings = Booking.objects.order_by('-created_at')[:5]
        recent_reviews = Review.objects.order_by('-created_at')[:5]
    
    # User growth chart data (last 30 days from filter_date or today)
    chart_base_date = filter_date if filter_date_str else today
    user_growth = []
    for i in range(29, -1, -1):
        date = chart_base_date - timedelta(days=i)
        start_dt, end_dt = get_date_range_for_filter(date)
        count = User.objects.filter(
            date_joined__gte=start_dt, 
            date_joined__lte=end_dt
        ).count()
        user_growth.append({
            'date': date.strftime('%m/%d'),
            'count': count
        })
    
    # Recent user registrations (last 10 users)
    recent_registrations = []
    if filter_date_str:
        start_datetime, end_datetime = get_date_range_for_filter(filter_date)
        recent_reg_users = User.objects.filter(
            date_joined__gte=start_datetime, 
            date_joined__lte=end_datetime
        ).order_by('-date_joined')[:10]
    else:
        recent_reg_users = User.objects.order_by('-date_joined')[:10]
    
    for user in recent_reg_users:
        recent_registrations.append({
            'username': user.username,
            'email': user.email,
            'role': user.get_role_display(),
            'date': user.date_joined.strftime('%Y-%m-%d %H:%M')
        })
    
    # Booking trends chart data (last 30 days)
    booking_trends = []
    for i in range(29, -1, -1):
        date = chart_base_date - timedelta(days=i)
        start_dt, end_dt = get_date_range_for_filter(date)
        count = Booking.objects.filter(
            created_at__gte=start_dt, 
            created_at__lte=end_dt
        ).count()
        booking_trends.append({
            'date': date.strftime('%m/%d'),
            'count': count
        })
    
    # Booking status distribution (filtered by date if provided)
    if filter_date_str:
        booking_stats = {
            'pending': Booking.objects.filter(status='pending', created_at__date__lte=filter_date).count(),
            'confirmed': Booking.objects.filter(status='confirmed', created_at__date__lte=filter_date).count(),
            'completed': Booking.objects.filter(status='completed', created_at__date__lte=filter_date).count(),
            'cancelled': Booking.objects.filter(status='cancelled', created_at__date__lte=filter_date).count(),
        }
    else:
        booking_stats = {
            'pending': Booking.objects.filter(status='pending').count(),
            'confirmed': Booking.objects.filter(status='confirmed').count(),
            'completed': Booking.objects.filter(status='completed').count(),
            'cancelled': Booking.objects.filter(status='cancelled').count(),
        }
    
    # Pending approvals
    pending_reviews = Review.objects.filter(is_approved=False).count()
    total_reviews = Review.objects.count()
    approved_reviews = Review.objects.filter(is_approved=True).count()
    total_contact_messages = ContactMessage.objects.count()
    
    # Subscription statistics
    from payments.models import UserSubscription, SubscriptionPlan, SubscriptionPayment
    
    # Total subscriptions (filtered by date if provided)
    if filter_date_str:
        start_datetime, end_datetime = get_date_range_for_filter(filter_date)
        total_subscriptions = UserSubscription.objects.filter(created_at__lte=end_datetime).count()
        active_subscriptions = UserSubscription.objects.filter(
            status='active', created_at__lte=end_datetime
        ).count()
        trial_subscriptions = UserSubscription.objects.filter(
            status='trial', created_at__lte=end_datetime
        ).count()
        # Monthly revenue from subscriptions
        subscription_revenue = SubscriptionPayment.objects.filter(
            status='completed', created_at__lte=end_datetime
        ).aggregate(total=Sum('amount'))['total'] or 0
    else:
        total_subscriptions = UserSubscription.objects.count()
        active_subscriptions = UserSubscription.objects.filter(status='active').count()
        trial_subscriptions = UserSubscription.objects.filter(status='trial').count()
        # Current month subscription revenue
        current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        subscription_revenue = SubscriptionPayment.objects.filter(
            status='completed', created_at__gte=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Create context dictionary
    context = {
        'total_users': total_users,
        'total_photographers': total_photographers,
        'total_clients': total_clients,
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'pending_bookings': pending_bookings,
        'total_revenue': total_revenue,
        'new_users_30d': new_users_30d,
        'new_bookings_30d': new_bookings_30d,
        'user_growth': json.dumps(user_growth),
        'booking_stats': json.dumps(booking_stats),
        'recent_users': recent_users,
        'recent_bookings': recent_bookings,
        'recent_reviews': recent_reviews,
        'pending_reviews': pending_reviews,
        'total_reviews': total_reviews,
        'approved_reviews': approved_reviews,
        'total_contact_messages': total_contact_messages,
        'filter_date': filter_date_str,  # Add filter date to context
        'filter_date_formatted': filter_date.strftime('%B %d, %Y') if filter_date_str else '',
        # Subscription statistics
        'total_subscriptions': total_subscriptions,
        'active_subscriptions': active_subscriptions,
        'trial_subscriptions': trial_subscriptions,
        'subscription_revenue': subscription_revenue,
        # Chart data
        'booking_trends': json.dumps(booking_trends),
        'recent_registrations': json.dumps(recent_registrations),
    }
    
    return render(request, 'admin_dashboard/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def users_management(request):
    """Manage all users"""
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    is_verified_filter = request.GET.get('verified', '')
    filter_date_str = request.GET.get('filter_date', '')
    
    # Handle date filtering with timezone awareness
    filter_date = parse_filter_date(filter_date_str)
    
    users = User.objects.all()
    
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(role=role_filter)
        
    if is_verified_filter:
        is_verified = is_verified_filter.lower() == 'true'
        users = users.filter(is_verified=is_verified)
    
    # Apply date filter if provided with timezone awareness
    if filter_date:
        start_datetime, end_datetime = get_date_range_for_filter(filter_date)
        users = users.filter(date_joined__gte=start_datetime, date_joined__lte=end_datetime)
    
    users = users.order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
        'is_verified_filter': is_verified_filter,
        'user_roles': User.Roles.choices,
        'filter_date': filter_date_str,
        'filter_date_formatted': filter_date.strftime('%B %d, %Y') if filter_date else '',
    }
    
    return render(request, 'admin_dashboard/users_management.html', context)

@login_required
@user_passes_test(is_admin)
def user_detail(request, user_id):
    """View and edit specific user"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            log_admin_activity(
                request.user, 'update', 'User', user.id,
                f"User {user.email}", f"Updated user details",
                request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f'User {user.email} updated successfully.')
            return redirect('admin_dashboard:user_detail', user_id=user.id)
    else:
        form = UserEditForm(instance=user)
    
    # User stats
    if user.role == User.Roles.PHOTOGRAPHER:
        user_stats = {
            'total_bookings': user.photographer_bookings.count(),
            'completed_bookings': user.photographer_bookings.filter(status='completed').count(),
            'total_photos': user.photos.count() if hasattr(user, 'photos') else 0,
            'total_reviews': user.reviews_received.count(),
            'average_rating': user.average_rating or 0,
        }
    else:
        user_stats = {
            'total_bookings': user.client_bookings.count(),
            'completed_bookings': user.client_bookings.filter(status='completed').count(),
            'total_reviews': user.reviews_made.count(),
        }
    
    recent_bookings = (
        user.photographer_bookings.all() if user.role == User.Roles.PHOTOGRAPHER 
        else user.client_bookings.all()
    )[:5]
    
    context = {
        'user_obj': user,  # Renamed to avoid conflict with request.user
        'form': form,
        'user_stats': user_stats,
        'recent_bookings': recent_bookings,
    }
    
    return render(request, 'admin_dashboard/user_detail.html', context)

@login_required
@user_passes_test(is_admin)
def user_details_json(request, user_id):
    """Get complete user details as JSON for modal view"""
    user = get_object_or_404(User, id=user_id)
    
    # Calculate user statistics
    if user.role == User.Roles.PHOTOGRAPHER:
        total_bookings = user.photographer_bookings.count()
        pending_bookings = user.photographer_bookings.filter(status='pending').count()
        completed_bookings = user.photographer_bookings.filter(status='completed').count()
        total_reviews = user.reviews_received.count()
    else:
        total_bookings = user.client_bookings.count()
        pending_bookings = user.client_bookings.filter(status='pending').count()
        completed_bookings = user.client_bookings.filter(status='completed').count()
        total_reviews = user.reviews_made.count() if hasattr(user, 'reviews_made') else 0
    
    # Get subscription payment information
    from payments.models import SubscriptionPayment, UserSubscription
    subscription_data = None
    try:
        # Get the user's subscription first, then get the latest payment
        user_subscription = user.subscription  # OneToOneField
        if user_subscription:
            latest_payment = user_subscription.payments.order_by('-created_at').first()
            if latest_payment:
                subscription_data = {
                    'amount': float(latest_payment.amount),
                    'currency': latest_payment.currency,
                    'plan_name': user_subscription.plan.display_name,
                    'plan_tier': user_subscription.plan.name,
                    'billing_cycle': user_subscription.billing_cycle,
                    'billing_cycle_display': user_subscription.get_billing_cycle_display(),
                    'payment_method': latest_payment.payment_method,
                    'status': latest_payment.status,
                    'status_display': latest_payment.get_status_display(),
                    'subscription_status': user_subscription.status,
                    'subscription_status_display': user_subscription.get_status_display(),
                    'transaction_id': str(latest_payment.transaction_id),
                    'created_at': latest_payment.created_at.strftime('%B %d, %Y at %I:%M %p'),
                    'start_date': user_subscription.start_date.strftime('%B %d, %Y') if user_subscription.start_date else None,
                    'end_date': user_subscription.end_date.strftime('%B %d, %Y') if user_subscription.end_date else None,
                    
                    # Payment method specific details
                    'card_brand': latest_payment.card_brand or None,
                    'card_last_four': latest_payment.card_last_four or None,
                    'cardholder_name': latest_payment.cardholder_name or None,
                    'mobile_money_provider': latest_payment.mobile_money_provider or None,
                    'mobile_money_phone': latest_payment.mobile_money_phone or None,
                    'paypal_email': latest_payment.paypal_email or None,
                }
    except UserSubscription.DoesNotExist:
        pass
    
    # Build response data
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'full_name': user.get_full_name() if user.get_full_name() else None,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': user.role,
        'role_display': user.get_role_display(),
        'bio': user.bio,
        'profile_picture': user.profile_picture.url if user.profile_picture else None,
        'gravatar_url': user.get_gravatar_url(80),
        'location': user.location,
        'contact_info': user.contact_info,
        'is_verified': user.is_verified,
        'is_active': user.is_active,
        'is_staff': user.is_staff,
        'date_joined': user.date_joined.strftime('%B %d, %Y at %I:%M %p'),
        'last_login': user.last_login.strftime('%B %d, %Y at %I:%M %p') if user.last_login else None,
        
        # Professional details (photographer-specific)
        'price': str(user.price) if user.price else None,
        'badges': user.badges if user.badges else None,
        'certifications': user.certifications if user.certifications else None,
        'awards': user.awards if user.awards else None,
        'social_proof': user.social_proof if user.social_proof else None,
        'average_rating': user.average_rating,
        
        # Activity statistics
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'completed_bookings': completed_bookings,
        'total_reviews': total_reviews,
        
        # Subscription payment information
        'subscription': subscription_data,
    }
    
    return JsonResponse({'success': True, 'user': user_data})

@login_required
@user_passes_test(is_admin)
@require_POST
def toggle_user_verification(request, user_id):
    """Toggle user verification status"""
    user = get_object_or_404(User, id=user_id)
    user.is_verified = not user.is_verified
    user.save()
    
    action = 'approve' if user.is_verified else 'reject'
    log_admin_activity(
        request.user, action, 'User', user.id,
        f"User {user.email}", f"{'Verified' if user.is_verified else 'Unverified'} user",
        request.META.get('REMOTE_ADDR')
    )
    
    status = 'verified' if user.is_verified else 'unverified'
    messages.success(request, f'User {user.email} has been {status}.')
    
    return JsonResponse({'success': True, 'is_verified': user.is_verified})

@login_required
@user_passes_test(is_admin)
@require_POST
def suspend_user(request, user_id):
    """Suspend/activate user account"""
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    
    action = 'activate' if user.is_active else 'suspend'
    log_admin_activity(
        request.user, action, 'User', user.id,
        f"User {user.email}", f"{'Activated' if user.is_active else 'Suspended'} user account",
        request.META.get('REMOTE_ADDR')
    )
    
    status = 'activated' if user.is_active else 'suspended'
    messages.success(request, f'User {user.email} has been {status}.')
    
    return JsonResponse({'success': True, 'is_active': user.is_active})

@login_required
@user_passes_test(is_admin)
def booking_details_json(request, booking_id):
    """Get complete booking details as JSON for modal view"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Get client information
    if booking.client:
        client_name = booking.client.get_full_name() or booking.client.username
        client_email = booking.client.email
        client_phone = booking.client.contact_info
        client_avatar = booking.client.profile_picture.url if booking.client.profile_picture else booking.client.get_gravatar_url(60)
        client_id = booking.client.id
    else:
        client_name = booking.client_name or 'N/A'
        client_email = booking.client_email or 'N/A'
        client_phone = booking.client_phone
        client_avatar = None
        client_id = None
    
    # Get photographer information
    photographer_name = booking.photographer.get_full_name() or booking.photographer.username
    photographer_email = booking.photographer.email
    photographer_phone = booking.photographer.contact_info
    photographer_avatar = booking.photographer.profile_picture.url if booking.photographer.profile_picture else booking.photographer.get_gravatar_url(60)
    photographer_price = str(booking.photographer.price) if booking.photographer.price else None
    
    # Calculate expected payment amount (from photographer's price or AI pricing)
    expected_amount = None
    if booking.photographer.price:
        expected_amount = float(booking.photographer.price)
    else:
        # Try to get AI-generated price
        try:
            ai_price = booking.simulate_ai_pricing()
            if ai_price:
                expected_amount = float(ai_price)
        except:
            pass
    
    # Get payment transaction information (get the latest transaction)
    payment_data = None
    transaction = booking.transactions.order_by('-created_at').first()
    if transaction:
        payment_data = {
            'amount': float(transaction.amount),
            'currency': transaction.currency,
            'payment_method': transaction.payment_method,
            'payment_method_display': transaction.get_payment_method_display(),
            'status': transaction.status,
            'status_display': transaction.get_status_display(),
            'transaction_id': transaction.transaction_id,
            'created_at': transaction.created_at.strftime('%B %d, %Y at %I:%M %p'),
            
            # Payment method specific details
            'card_brand': transaction.card_brand,
            'card_last_four': transaction.card_last_four,
            'cardholder_name': transaction.cardholder_name,
            'mobile_money_provider': transaction.mobile_money_provider,
            'mobile_money_phone': transaction.mobile_money_phone,
            'paypal_email': transaction.paypal_email,
            'bank_name': transaction.bank_name,
            'bank_reference': transaction.bank_reference,
        }
    
    # Build response data
    booking_data = {
        'id': booking.id,
        'service_type': booking.service_type,
        'service_type_display': booking.get_service_type_display(),
        'date': booking.date.strftime('%B %d, %Y'),
        'time': booking.time.strftime('%I:%M %p'),
        'location': booking.location,
        'status': booking.status,
        'status_display': booking.get_status_display(),
        'payment_status': booking.payment_status,
        'payment_status_display': booking.get_payment_status_display(),
        'created_at': booking.created_at.strftime('%B %d, %Y at %I:%M %p'),
        
        # Client information
        'client_id': client_id,
        'client_name': client_name,
        'client_email': client_email,
        'client_phone': client_phone,
        'client_avatar': client_avatar,
        
        # Photographer information
        'photographer_id': booking.photographer.id,
        'photographer_name': photographer_name,
        'photographer_email': photographer_email,
        'photographer_phone': photographer_phone,
        'photographer_avatar': photographer_avatar,
        'photographer_price': photographer_price,
        
        # Payment information
        'payment': payment_data,
        'expected_amount': expected_amount,
    }
    
    return JsonResponse({'success': True, 'booking': booking_data})

@login_required
@user_passes_test(is_admin)
def bookings_management(request):
    """Manage all bookings"""
    from payments.models import Transaction
    from django.db.models import Sum, Count, Q
    from decimal import Decimal
    
    status_filter = request.GET.get('status', '')
    payment_filter = request.GET.get('payment', '')
    search_query = request.GET.get('search', '')
    filter_date_str = request.GET.get('filter_date', '')
    
    bookings = Booking.objects.select_related('client', 'photographer')
    
    # Handle date filtering with timezone awareness
    filter_date = parse_filter_date(filter_date_str)
    if filter_date:
        start_datetime, end_datetime = get_date_range_for_filter(filter_date)
        bookings = bookings.filter(created_at__gte=start_datetime, created_at__lte=end_datetime)
    
    if status_filter:
        bookings = bookings.filter(status=status_filter)
        
    if payment_filter:
        bookings = bookings.filter(payment_status=payment_filter)
        
    if search_query:
        bookings = bookings.filter(
            Q(client__email__icontains=search_query) |
            Q(photographer__email__icontains=search_query) |
            Q(service_type__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Calculate payment statistics for filtered bookings
    filtered_bookings_queryset = bookings
    
    # Get all transactions for these bookings
    booking_ids = list(filtered_bookings_queryset.values_list('id', flat=True))
    transactions = Transaction.objects.filter(booking_id__in=booking_ids)
    
    # Payment statistics
    total_paid = transactions.filter(status__in=['completed', 'paid']).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_pending = transactions.filter(status__in=['pending', 'held_escrow', 'processing']).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_failed = transactions.filter(status__in=['failed', 'cancelled']).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Count by payment method
    payment_methods = transactions.filter(status__in=['completed', 'paid']).values('payment_method').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')
    
    # Count by payment status
    paid_count = filtered_bookings_queryset.filter(payment_status='paid').count()
    pending_count = filtered_bookings_queryset.filter(payment_status='pending').count()
    failed_count = filtered_bookings_queryset.filter(payment_status='failed').count()
    
    bookings = bookings.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(bookings, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'payment_filter': payment_filter,
        'search_query': search_query,
        'filter_date': filter_date_str,
        'booking_statuses': Booking.STATUS_CHOICES,
        'payment_statuses': Booking.PAYMENT_STATUS_CHOICES,
        # Payment statistics
        'total_paid': total_paid,
        'total_pending': total_pending,
        'total_failed': total_failed,
        'paid_count': paid_count,
        'pending_count': pending_count,
        'failed_count': failed_count,
        'payment_methods': payment_methods,
    }
    
    return render(request, 'admin_dashboard/bookings_management.html', context)

@login_required
@user_passes_test(is_admin)
def reviews_management(request):
    """Manage all reviews"""
    approval_filter = request.GET.get('approved', '')
    search_query = request.GET.get('search', '')
    filter_date_str = request.GET.get('filter_date', '')
    
    reviews = Review.objects.select_related('reviewer', 'photographer', 'booking')
    
    # Handle date filtering with timezone awareness
    filter_date = parse_filter_date(filter_date_str)
    if filter_date:
        start_datetime, end_datetime = get_date_range_for_filter(filter_date)
        reviews = reviews.filter(created_at__gte=start_datetime, created_at__lte=end_datetime)
    
    if approval_filter:
        is_approved = approval_filter.lower() == 'true'
        reviews = reviews.filter(is_approved=is_approved)
        
    if search_query:
        reviews = reviews.filter(
            Q(reviewer__email__icontains=search_query) |
            Q(photographer__email__icontains=search_query) |
            Q(comment__icontains=search_query)
        )
    
    reviews = reviews.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(reviews, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'approval_filter': approval_filter,
        'search_query': search_query,
        'filter_date': filter_date_str,
    }
    
    return render(request, 'admin_dashboard/reviews_management.html', context)

@login_required
@user_passes_test(is_admin)
@require_POST
def approve_review(request, review_id):
    """Approve/disapprove review"""
    review = get_object_or_404(Review, id=review_id)
    review.is_approved = not review.is_approved
    review.save()
    
    action = 'approve' if review.is_approved else 'reject'
    # Handle both authenticated and anonymous reviews
    reviewer_info = review.reviewer.email if review.reviewer else f"Anonymous user: {review.anonymous_name}"
    log_admin_activity(
        request.user, action, 'Review', review.id,
        f"Review by {reviewer_info}", f"{'Approved' if review.is_approved else 'Rejected'} review",
        request.META.get('REMOTE_ADDR')
    )
    
    status = 'approved' if review.is_approved else 'rejected'
    messages.success(request, f'Review has been {status}.')
    
    return JsonResponse({'success': True, 'is_approved': review.is_approved})

@login_required
@user_passes_test(is_admin)
def review_details_json(request, review_id):
    """Return review details as JSON for modal display"""
    try:
        review = Review.objects.select_related('reviewer', 'photographer', 'booking').get(id=review_id)
        
        data = {
            'id': review.id,
            'reviewer_name': review.reviewer.get_full_name() if review.reviewer else review.anonymous_name,
            'reviewer_email': review.reviewer.email if review.reviewer else review.anonymous_email,
            'photographer_name': review.photographer.get_full_name(),
            'photographer_email': review.photographer.email,
            'overall_rating': review.overall_rating,
            'quality_rating': review.quality_rating,
            'professionalism_rating': review.professionalism_rating,
            'communication_rating': review.communication_rating,
            'value_rating': review.value_rating,
            'title': review.title,
            'comment': review.comment,
            'is_approved': review.is_approved,
            'is_verified': review.is_verified,
            'is_featured': review.is_featured,
            'created_at': review.created_at.strftime('%B %d, %Y at %I:%M %p'),
            'updated_at': review.updated_at.strftime('%B %d, %Y at %I:%M %p'),
            'booking_id': review.booking.id if review.booking else None,
            'categories': [cat.name for cat in review.categories.all()],
            'helpfulness_votes': review.helpfulness_votes,
            'total_votes': review.total_votes,
        }
        
        return JsonResponse(data)
    except Review.DoesNotExist:
        return JsonResponse({'error': 'Review not found'}, status=404)

@login_required
@user_passes_test(is_admin)
def analytics_dashboard(request):
    """Advanced analytics dashboard"""
    # Time period filter
    period = request.GET.get('period', '30')  # days
    filter_date_str = request.GET.get('filter_date', '')
    
    try:
        days = int(period)
    except (ValueError, TypeError):
        days = 30
    
    # Handle date filtering with timezone awareness
    filter_date = parse_filter_date(filter_date_str)
    
    if filter_date:
        # If specific date is selected, show data for that date and period around it
        end_date = filter_date
        start_date = filter_date - timedelta(days=days)
    else:
        # Default behavior
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
    
    # User registration trends - using cumulative data showing growth over time
    user_registrations = []
    photographer_registrations = []
    client_registrations = []
    
    # Get all users up to the end date
    all_users = User.objects.filter(date_joined__lte=timezone.make_aware(datetime.combine(end_date, datetime.max.time())))
    
    for i in range(days, -1, -1):
        date = end_date - timedelta(days=i)
        date_end = timezone.make_aware(datetime.combine(date, datetime.max.time()))
        
        # Count cumulative registrations up to this date
        users_count = all_users.filter(date_joined__lte=date_end).count()
        photographers_count = all_users.filter(
            date_joined__lte=date_end, 
            role=User.Roles.PHOTOGRAPHER
        ).count()
        clients_count = all_users.filter(
            date_joined__lte=date_end, 
            role=User.Roles.CLIENT
        ).count()
        
        user_registrations.append({'date': date.strftime('%m/%d'), 'count': users_count})
        photographer_registrations.append({'date': date.strftime('%m/%d'), 'count': photographers_count})
        client_registrations.append({'date': date.strftime('%m/%d'), 'count': clients_count})
    
    # Booking trends - using cumulative data showing growth over time
    booking_trends = []
    revenue_trends = []
    
    # Get all bookings and transactions up to the end date
    all_bookings = Booking.objects.filter(created_at__lte=timezone.make_aware(datetime.combine(end_date, datetime.max.time())))
    all_transactions = Transaction.objects.filter(
        created_at__lte=timezone.make_aware(datetime.combine(end_date, datetime.max.time())),
        status='paid'
    )
    
    for i in range(days, -1, -1):
        date = end_date - timedelta(days=i)
        date_end = timezone.make_aware(datetime.combine(date, datetime.max.time()))
        
        # Count cumulative bookings up to this date
        bookings_count = all_bookings.filter(created_at__lte=date_end).count()
        
        # Calculate cumulative revenue up to this date
        revenue = all_transactions.filter(created_at__lte=date_end).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        booking_trends.append({'date': date.strftime('%m/%d'), 'count': bookings_count})
        revenue_trends.append({'date': date.strftime('%m/%d'), 'amount': float(revenue)})
    
    # Top photographers by bookings (top 5)
    top_photographers = User.objects.filter(
        role=User.Roles.PHOTOGRAPHER
    ).annotate(
        booking_count=Count('photographer_bookings'),
        completed_bookings=Count(
            'photographer_bookings',
            filter=Q(photographer_bookings__status='completed')
        )
    ).order_by('-booking_count')[:5]
    
    # Create timezone-aware datetime objects for filtering
    start_datetime = None
    end_datetime = None
    
    if start_date:
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    if end_date:
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
    
    # Service type popularity (filtered by date range, top 5)
    if start_datetime and end_datetime:
        service_popularity = Booking.objects.filter(
            created_at__gte=start_datetime,
            created_at__lte=end_datetime
        ).values('service_type').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
    else:
        service_popularity = Booking.objects.values('service_type').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
    
    # Calculate totals filtered by date range
    if start_datetime and end_datetime:
        # Filter all metrics by the selected date range
        total_users = User.objects.filter(
            date_joined__gte=start_datetime,
            date_joined__lte=end_datetime
        ).count()
        total_photographers = User.objects.filter(
            date_joined__gte=start_datetime,
            date_joined__lte=end_datetime,
            role=User.Roles.PHOTOGRAPHER
        ).count()
        total_bookings = Booking.objects.filter(
            created_at__gte=start_datetime,
            created_at__lte=end_datetime
        ).count()
        total_revenue = Transaction.objects.filter(
            created_at__gte=start_datetime,
            created_at__lte=end_datetime,
            status='paid'
        ).aggregate(total=Sum('amount'))['total'] or 0
    else:
        # Show all-time totals when no date filter is applied
        total_users = User.objects.count()
        total_photographers = User.objects.filter(role=User.Roles.PHOTOGRAPHER).count()
        total_bookings = Booking.objects.count()
        total_revenue = Transaction.objects.filter(status='paid').aggregate(
            total=Sum('amount')
        )['total'] or 0
    
    # Period-specific metrics for comparison (new vs total in period)
    # Use the period start_date for "this period" calculations
    period_start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    
    new_users = User.objects.filter(date_joined__gte=period_start_datetime).count()
    new_photographers = User.objects.filter(
        date_joined__gte=period_start_datetime, role=User.Roles.PHOTOGRAPHER
    ).count()
    new_bookings = Booking.objects.filter(created_at__gte=period_start_datetime).count()
    period_revenue = Transaction.objects.filter(
        created_at__gte=period_start_datetime, status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'period': period,
        'user_registrations': json.dumps(user_registrations),
        'photographer_registrations': json.dumps(photographer_registrations),
        'client_registrations': json.dumps(client_registrations),
        'booking_trends': json.dumps(booking_trends),
        'revenue_trends': json.dumps(revenue_trends),
        'top_photographers': top_photographers,
        'service_popularity': service_popularity,
        # Totals
        'total_users': total_users,
        'total_photographers': total_photographers,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        # Period metrics
        'new_users': new_users,
        'new_photographers': new_photographers,
        'new_bookings': new_bookings,
        'period_revenue': period_revenue,
        # Filter date
        'filter_date': filter_date_str,
        'filter_date_formatted': filter_date.strftime('%B %d, %Y') if filter_date else '',
    }
    
    return render(request, 'admin_dashboard/analytics.html', context)

@login_required
@user_passes_test(is_admin)
def notifications_management(request):
    """Manage system notifications with email support"""
    if request.method == 'POST':
        form = SystemNotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.created_by = request.user
            
            # Set email subject if not provided
            if not notification.email_subject:
                notification.email_subject = notification.title
            
            # Set email status based on delivery method and send_immediately
            if notification.delivery_method in ['email', 'both']:
                if notification.send_immediately:
                    notification.email_status = 'pending'
                else:
                    notification.email_status = 'draft'
            else:
                notification.email_status = 'pending'  # For in-app only
            
            notification.save()
            
            # Send emails if required and send_immediately is True
            if notification.delivery_method in ['email', 'both'] and notification.send_immediately:
                try:
                    result = NotificationEmailService.send_notification_email(notification)
                    if result['success']:
                        messages.success(
                            request, 
                            f'Notification created and {result["message"]}!'
                        )
                    else:
                        messages.warning(
                            request,
                            f'Notification created but email sending failed: {result["message"]}'
                        )
                except Exception as e:
                    messages.error(
                        request,
                        f'Notification created but email sending failed: {str(e)}'
                    )
            else:
                messages.success(request, 'Notification created successfully.')
            
            log_admin_activity(
                request.user, 'create', 'SystemNotification', notification.id,
                f"Notification: {notification.title}", 
                f"Created notification for {notification.target_users}",
                request.META.get('REMOTE_ADDR')
            )
            
            return redirect('admin_dashboard:notifications_management')
        else:
            # Form is not valid - display errors
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f'Form error: {error}')
                    else:
                        field_name = form.fields[field].label or field.replace('_', ' ').title()
                        messages.error(request, f'{field_name}: {error}')
    else:
        form = SystemNotificationForm()
    
    # Handle date filtering with timezone awareness
    filter_date_str = request.GET.get('filter_date', '')
    notifications = SystemNotification.objects.all()
    
    filter_date = parse_filter_date(filter_date_str)
    if filter_date:
        start_datetime, end_datetime = get_date_range_for_filter(filter_date)
        notifications = notifications.filter(created_at__gte=start_datetime, created_at__lte=end_datetime)
    
    notifications = notifications.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'filter_date': filter_date_str,
    }
    
    return render(request, 'admin_dashboard/notifications.html', context)

@login_required
@user_passes_test(is_admin)
def send_notification_email(request, notification_id):
    """Send email for a notification manually"""
    notification = get_object_or_404(SystemNotification, id=notification_id)
    
    if request.method == 'POST':
        if notification.delivery_method not in ['email', 'both']:
            messages.error(request, 'This notification is not configured for email delivery.')
            return redirect('admin_dashboard:notifications_management')
        
        try:
            result = NotificationEmailService.send_notification_email(notification)
            if result['success']:
                messages.success(request, result['message'])
                
                log_admin_activity(
                    request.user, 'update', 'SystemNotification', notification.id,
                    f"Notification: {notification.title}", 
                    f"Sent emails to {result.get('sent_count', 0)} users",
                    request.META.get('REMOTE_ADDR')
                )
            else:
                messages.error(request, f'Email sending failed: {result["message"]}')
        except Exception as e:
            messages.error(request, f'Error sending emails: {str(e)}')
    
    return redirect('admin_dashboard:notifications_management')

@login_required
@user_passes_test(is_admin)
def preview_notification_email(request, notification_id):
    """Preview email for a notification"""
    notification = get_object_or_404(SystemNotification, id=notification_id)
    
    if notification.delivery_method not in ['email', 'both']:
        messages.error(request, 'This notification is not configured for email delivery.')
        return redirect('admin_dashboard:notifications_management')
    
    try:
        preview_result = NotificationEmailService.preview_notification_email(notification)
        if preview_result['success']:
            context = {
                'notification': notification,
                'preview': preview_result,
                'recipient_count': preview_result.get('recipient_count', 0),
            }
            return render(request, 'admin_dashboard/email_preview.html', context)
        else:
            messages.error(request, f'Preview failed: {preview_result["message"]}')
    except Exception as e:
        messages.error(request, f'Error generating preview: {str(e)}')
    
    return redirect('admin_dashboard:notifications_management')

@login_required
@user_passes_test(is_admin)
@require_POST
def toggle_notification_status(request, notification_id):
    """Toggle notification active status"""
    notification = get_object_or_404(SystemNotification, id=notification_id)
    notification.is_active = not notification.is_active
    notification.save()
    
    status = 'activated' if notification.is_active else 'deactivated'
    log_admin_activity(
        request.user, 'update', 'SystemNotification', notification.id,
        f"Notification: {notification.title}", f"Notification {status}",
        request.META.get('REMOTE_ADDR')
    )
    
    messages.success(request, f'Notification has been {status}.')
    return JsonResponse({'success': True, 'is_active': notification.is_active})

@login_required
@user_passes_test(is_admin)
def activity_logs(request):
    """View admin activity logs"""
    admin_filter = request.GET.get('admin', '')
    action_filter = request.GET.get('action', '')
    model_filter = request.GET.get('model', '')
    filter_date_str = request.GET.get('filter_date', '')
    
    logs = AdminActivityLog.objects.select_related('admin_user')
    
    # Handle date filtering with timezone awareness
    filter_date = parse_filter_date(filter_date_str)
    if filter_date:
        start_datetime, end_datetime = get_date_range_for_filter(filter_date)
        logs = logs.filter(timestamp__gte=start_datetime, timestamp__lte=end_datetime)
    
    if admin_filter:
        logs = logs.filter(admin_user__email__icontains=admin_filter)
        
    if action_filter:
        logs = logs.filter(action=action_filter)
        
    if model_filter:
        logs = logs.filter(target_model__icontains=model_filter)
    
    logs = logs.order_by('-timestamp')
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'admin_filter': admin_filter,
        'action_filter': action_filter,
        'model_filter': model_filter,
        'filter_date': filter_date_str,
        'action_choices': AdminActivityLog.ACTION_CHOICES,
    }
    
    return render(request, 'admin_dashboard/activity_logs.html', context)

@login_required
@user_passes_test(is_admin)
def export_data(request):
    """Export platform data as CSV"""
    data_type = request.GET.get('type', 'users')
    
    response = HttpResponse(content_type='text/csv')
    
    if data_type == 'users':
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['Email', 'First Name', 'Last Name', 'Role', 'Verified', 'Date Joined', 'Last Login'])
        
        for user in User.objects.all():
            writer.writerow([
                user.email, user.first_name, user.last_name, user.role,
                user.is_verified, user.date_joined, user.last_login
            ])
            
    elif data_type == 'bookings':
        response['Content-Disposition'] = 'attachment; filename="bookings_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['Client', 'Photographer', 'Service', 'Date', 'Status', 'Payment Status', 'Created'])
        
        for booking in Booking.objects.select_related('client', 'photographer'):
            writer.writerow([
                booking.client.email if booking.client else booking.client_email,
                booking.photographer.email, booking.service_type, booking.date,
                booking.status, booking.payment_status, booking.created_at
            ])
            
    elif data_type == 'reviews':
        response['Content-Disposition'] = 'attachment; filename="reviews_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['Reviewer', 'Photographer', 'Rating', 'Comment', 'Approved', 'Created'])
        
        for review in Review.objects.select_related('reviewer', 'photographer'):
            writer.writerow([
                review.reviewer.email, review.photographer.email, review.rating,
                review.comment[:100], review.is_approved, review.created_at
            ])
    
    return response


# === New Notification Email Views ===

@login_required
@user_passes_test(is_admin)
@require_POST
def preview_notification_email(request):
    """Preview email for new notification (without saving)"""
    form = SystemNotificationForm(request.POST)
    
    if form.is_valid():
        # Create temporary notification object for preview
        temp_notification = form.save(commit=False)
        temp_notification.pk = 0  # Temporary ID for preview
        
        try:
            from .email_service import NotificationEmailService
            email_service = NotificationEmailService()
            
            # Generate preview HTML
            preview_html = email_service.generate_preview_html(temp_notification)
            
            return JsonResponse({
                'success': True,
                'preview_html': preview_html
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Invalid form data',
            'form_errors': form.errors
        })

@login_required
@user_passes_test(is_admin)
@require_POST
def send_notification_email(request):
    """Send email for new notification"""
    form = SystemNotificationForm(request.POST)
    
    if form.is_valid():
        # Save the notification
        notification = form.save()
        
        try:
            from .email_service import NotificationEmailService
            email_service = NotificationEmailService()
            
            # Send emails if email delivery is enabled
            if notification.delivery_method in ['email', 'both']:
                result = email_service.send_notification_email(notification)
                
                if result['success']:
                    sent_count = result['sent_count']
                    
                    # Log the activity
                    log_admin_activity(
                        request.user, 'create', 'SystemNotification', notification.id,
                        f"Notification: {notification.title}", 
                        f"Created and sent to {sent_count} recipients",
                        request.META.get('REMOTE_ADDR')
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'sent_count': sent_count,
                        'message': f'Notification created and emails sent to {sent_count} recipients'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': result['message']
                    })
            else:
                # Log activity for in-app only notifications
                log_admin_activity(
                    request.user, 'create', 'SystemNotification', notification.id,
                    f"Notification: {notification.title}", "Created (in-app only)",
                    request.META.get('REMOTE_ADDR')
                )
                
                return JsonResponse({
                    'success': True,
                    'sent_count': 0,
                    'message': 'Notification created (in-app only)'
                })
                
        except Exception as e:
            # If email fails, still keep the notification but mark email as failed
            notification.email_status = 'failed'
            notification.save()
            
            return JsonResponse({
                'success': False,
                'error': f'Notification created but email sending failed: {str(e)}'
            })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Invalid form data',
            'form_errors': form.errors
        })

@login_required
@user_passes_test(is_admin)
def get_recipient_count(request):
    """Get count of recipients for target user selection"""
    target = request.GET.get('target', 'all')
    
    try:
        # Create temporary notification to use the queryset method
        temp_notification = SystemNotification(target_users=target)
        queryset = temp_notification.get_target_users_queryset()
        count = queryset.count()
        
        return JsonResponse({
            'success': True,
            'count': count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'count': 0
        })

@login_required
@user_passes_test(is_admin)
@require_POST
def preview_existing_notification_email(request, notification_id):
    """Preview email for existing notification"""
    notification = get_object_or_404(SystemNotification, id=notification_id)
    
    try:
        from .email_service import NotificationEmailService
        email_service = NotificationEmailService()
        
        # Generate preview HTML
        preview_html = email_service.generate_preview_html(notification)
        
        return JsonResponse({
            'success': True,
            'preview_html': preview_html
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@user_passes_test(is_admin)
@require_POST
def send_existing_notification_email(request, notification_id):
    """Send email for existing notification"""
    notification = get_object_or_404(SystemNotification, id=notification_id)
    
    try:
        from .email_service import NotificationEmailService
        email_service = NotificationEmailService()
        
        # Send emails
        result = email_service.send_notification_email(notification)
        
        if result['success']:
            sent_count = result['sent_count']
            
            # Log the activity
            log_admin_activity(
                request.user, 'update', 'SystemNotification', notification.id,
                f"Notification: {notification.title}", 
                f"Emails sent to {sent_count} recipients",
                request.META.get('REMOTE_ADDR')
            )
            
            return JsonResponse({
                'success': True,
                'sent_count': sent_count
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@user_passes_test(is_admin)
@require_POST
def toggle_notification(request, notification_id):
    """Toggle notification active status"""
    import json
    data = json.loads(request.body)
    active = data.get('active')
    
    notification = get_object_or_404(SystemNotification, id=notification_id)
    notification.is_active = active
    notification.save()
    
    status = 'activated' if active else 'deactivated'
    log_admin_activity(
        request.user, 'update', 'SystemNotification', notification.id,
        f"Notification: {notification.title}", f"Notification {status}",
        request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({
        'success': True,
        'is_active': notification.is_active
    })

@login_required
@user_passes_test(is_admin)
@require_POST
def delete_notification(request, notification_id):
    """Delete notification"""
    notification = get_object_or_404(SystemNotification, id=notification_id)
    title = notification.title
    
    # Log the activity before deleting
    log_admin_activity(
        request.user, 'delete', 'SystemNotification', notification.id,
        f"Notification: {title}", "Notification deleted",
        request.META.get('REMOTE_ADDR')
    )
    
    notification.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'Notification "{title}" has been deleted'
    })


# Subscription Management Views
@login_required
@user_passes_test(is_admin)
def subscription_plans_management(request):
    """View for managing subscription plans"""
    from payments.models import SubscriptionPlan, UserSubscription
    
    plans = SubscriptionPlan.objects.all().order_by('price_monthly')
    
    # Get statistics for each plan
    plan_stats = {}
    for plan in plans:
        plan_stats[plan.id] = {
            'total_subscribers': UserSubscription.objects.filter(plan=plan).count(),
            'active_subscribers': UserSubscription.objects.filter(plan=plan, status='active').count(),
            'monthly_revenue': UserSubscription.objects.filter(
                plan=plan, 
                status='active'
            ).aggregate(total=Sum('plan__price_monthly'))['total'] or 0
        }
    
    context = {
        'plans': plans,
        'plan_stats': plan_stats,
        'total_plans': plans.count(),
    }
    
    return render(request, 'admin_dashboard/subscription_plans.html', context)


@login_required
@user_passes_test(is_admin)
def subscription_users_management(request):
    """View for managing user subscriptions"""
    from payments.models import UserSubscription
    
    subscriptions = UserSubscription.objects.select_related('user', 'plan').order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        subscriptions = subscriptions.filter(status=status_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        subscriptions = subscriptions.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(subscriptions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total': UserSubscription.objects.count(),
        'active': UserSubscription.objects.filter(status='active').count(),
        'trial': UserSubscription.objects.filter(status='trial').count(),
        'expired': UserSubscription.objects.filter(status='expired').count(),
        'cancelled': UserSubscription.objects.filter(status='cancelled').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'admin_dashboard/subscription_users.html', context)


@login_required
@user_passes_test(is_admin)
def subscription_payments_management(request):
    """View for managing subscription payments"""
    from payments.models import SubscriptionPayment
    
    payments = SubscriptionPayment.objects.select_related('subscription__user').order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    # Date filter
    date_filter = request.GET.get('date')
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            payments = payments.filter(created_at__date=filter_date)
        except ValueError:
            pass
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        payments = payments.filter(
            Q(subscription__user__username__icontains=search_query) |
            Q(subscription__user__email__icontains=search_query) |
            Q(transaction_id__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_payments': SubscriptionPayment.objects.count(),
        'completed_payments': SubscriptionPayment.objects.filter(status='completed').count(),
        'pending_payments': SubscriptionPayment.objects.filter(status='pending').count(),
        'failed_payments': SubscriptionPayment.objects.filter(status='failed').count(),
        'total_revenue': SubscriptionPayment.objects.filter(status='completed').aggregate(
            total=Sum('amount'))['total'] or 0,
        'monthly_revenue': SubscriptionPayment.objects.filter(
            status='completed',
            created_at__month=timezone.now().month,
            created_at__year=timezone.now().year
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'search_query': search_query,
    }
    
    return render(request, 'admin_dashboard/subscription_payments.html', context)


@login_required
@user_passes_test(is_admin)
def subscription_stats_api(request):
    """API endpoint to get subscription statistics for admin template"""
    from payments.models import UserSubscription, SubscriptionPayment
    from django.db.models import Sum
    from django.utils import timezone
    
    # Get subscription statistics
    total_subscriptions = UserSubscription.objects.count()
    active_subscriptions = UserSubscription.objects.filter(status='active').count()
    
    # Current month subscription revenue
    current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_revenue = SubscriptionPayment.objects.filter(
        status='completed', 
        created_at__gte=current_month_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    return JsonResponse({
        'total_subscriptions': total_subscriptions,
        'active_subscriptions': active_subscriptions,
        'monthly_revenue': float(monthly_revenue),
    })


@login_required
@user_passes_test(is_admin)
def payment_details_api(request, payment_id):
    """API endpoint to get payment details"""
    from payments.models import SubscriptionPayment
    
    # Add debug logging
    print(f"Payment details API called for payment_id: {payment_id}")
    
    try:
        payment = SubscriptionPayment.objects.select_related(
            'subscription__user',
            'subscription__plan'
        ).get(id=payment_id)
        
        data = {
            'id': payment.id,
            'transaction_id': payment.transaction_id or payment.id,
            'amount': float(payment.amount),
            'currency': payment.currency or 'RWF',
            'status': payment.status,
            'payment_method': payment.payment_method,
            'created_at': payment.created_at.strftime('%B %d, %Y at %I:%M %p'),
            'updated_at': payment.updated_at.strftime('%B %d, %Y at %I:%M %p') if payment.updated_at else None,
            'notes': payment.notes if hasattr(payment, 'notes') else None,
        }
        
        # Add user information
        if payment.subscription and payment.subscription.user:
            data['user'] = {
                'id': payment.subscription.user.id,
                'username': payment.subscription.user.username,
                'email': payment.subscription.user.email,
            }
        
        # Add plan information
        if payment.subscription and payment.subscription.plan:
            data['plan'] = {
                'id': payment.subscription.plan.id,
                'name': payment.subscription.plan.display_name,
                'price': float(payment.subscription.plan.price_monthly),
                'billing_cycle': 'monthly',
            }
            
        # Add subscription status
        if payment.subscription:
            data['subscription_status'] = payment.subscription.status.title()
        
        return JsonResponse(data)
        
    except SubscriptionPayment.DoesNotExist:
        return JsonResponse({'error': 'Payment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(is_admin)
def admin_redirect_notice(request):
    """
    Display a notice page for users who try to access Django admin subscription pages
    """
    context = {
        'page_title': 'Admin Redirect Notice',
        'message': 'Subscription management has been moved to our custom admin dashboard for a better experience.',
        'dashboard_url': '/admin-dashboard/',
        'subscription_plans_url': '/admin-dashboard/subscriptions/plans/',
        'subscription_users_url': '/admin-dashboard/subscriptions/users/',
        'subscription_payments_url': '/admin-dashboard/subscriptions/payments/',
    }
    return render(request, 'admin_dashboard/admin_redirect_notice.html', context)


@login_required
@user_passes_test(is_admin)
def platform_revenue_management(request):
    """Enhanced platform revenue management view"""
    from payments.models import PlatformRevenue, Transaction, SubscriptionPayment
    from django.db.models import Sum, Count, Avg
    from decimal import Decimal
    
    # Date filtering
    filter_date_str = request.GET.get('filter_date', '')
    period = request.GET.get('period', '30')  # days
    
    try:
        days = int(period)
    except (ValueError, TypeError):
        days = 30
    
    # Calculate date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    if filter_date_str:
        filter_date = parse_filter_date(filter_date_str)
        if filter_date:
            end_date = filter_date
            start_date = end_date - timedelta(days=days)
    
    # Get platform revenue from commissions
    commission_revenue = Transaction.objects.filter(
        transaction_type=Transaction.TransactionType.CLIENT_PAYMENT,
        status=Transaction.TransactionStatus.COMPLETED,
        completed_at__date__gte=start_date,
        completed_at__date__lte=end_date
    ).aggregate(
        total_commission=Sum('commission_amount'),
        total_processing_fee=Sum('processing_fee'),
        total_amount=Sum('amount'),
        transaction_count=Count('id')
    )
    
    # Get subscription revenue
    subscription_revenue_data = SubscriptionPayment.objects.filter(
        status='completed',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).aggregate(
        total_amount=Sum('amount'),
        payment_count=Count('id')
    )
    
    # Calculate totals
    total_commission = commission_revenue['total_commission'] or Decimal('0')
    total_processing_fee = commission_revenue['total_processing_fee'] or Decimal('0')
    total_booking_revenue = commission_revenue['total_amount'] or Decimal('0')
    booking_transaction_count = commission_revenue['transaction_count'] or 0
    
    total_subscription_revenue = subscription_revenue_data['total_amount'] or Decimal('0')
    subscription_payment_count = subscription_revenue_data['payment_count'] or 0
    
    # Net platform revenue (commission from bookings + subscription revenue)
    net_platform_revenue = total_commission + total_subscription_revenue
    
    # Daily revenue trends
    daily_revenue = []
    for i in range(days - 1, -1, -1):
        date = end_date - timedelta(days=i)
        
        # Commission revenue for the day
        day_commission = Transaction.objects.filter(
            transaction_type=Transaction.TransactionType.CLIENT_PAYMENT,
            status=Transaction.TransactionStatus.COMPLETED,
            completed_at__date=date
        ).aggregate(total=Sum('commission_amount'))['total'] or Decimal('0')
        
        # Subscription revenue for the day
        day_subscription = SubscriptionPayment.objects.filter(
            status='completed',
            created_at__date=date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        daily_revenue.append({
            'date': date.strftime('%m/%d'),
            'commission': float(day_commission),
            'subscription': float(day_subscription),
            'total': float(day_commission + day_subscription)
        })
    
    # Revenue breakdown by payment method
    payment_method_breakdown = Transaction.objects.filter(
        transaction_type=Transaction.TransactionType.CLIENT_PAYMENT,
        status=Transaction.TransactionStatus.COMPLETED,
        completed_at__date__gte=start_date,
        completed_at__date__lte=end_date
    ).values('payment_method').annotate(
        total=Sum('commission_amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Top earning photographers
    top_photographers = Transaction.objects.filter(
        transaction_type=Transaction.TransactionType.CLIENT_PAYMENT,
        status=Transaction.TransactionStatus.COMPLETED,
        completed_at__date__gte=start_date,
        completed_at__date__lte=end_date
    ).values('booking__photographer__username', 'booking__photographer__email').annotate(
        total_bookings=Count('id'),
        platform_commission=Sum('commission_amount')
    ).order_by('-platform_commission')[:10]
    
    # Recent transactions
    recent_transactions = Transaction.objects.filter(
        transaction_type=Transaction.TransactionType.CLIENT_PAYMENT,
        status=Transaction.TransactionStatus.COMPLETED
    ).select_related('booking__photographer', 'booking__client', 'user').order_by('-completed_at')[:15]
    
    # Statistics summary
    avg_commission_per_booking = total_commission / booking_transaction_count if booking_transaction_count > 0 else Decimal('0')
    avg_subscription_payment = total_subscription_revenue / subscription_payment_count if subscription_payment_count > 0 else Decimal('0')
    
    context = {
        'period': period,
        'filter_date': filter_date_str,
        'start_date': start_date,
        'end_date': end_date,
        
        # Revenue totals
        'net_platform_revenue': net_platform_revenue,
        'total_commission': total_commission,
        'total_subscription_revenue': total_subscription_revenue,
        'total_processing_fee': total_processing_fee,
        'total_booking_revenue': total_booking_revenue,
        
        # Transaction counts
        'booking_transaction_count': booking_transaction_count,
        'subscription_payment_count': subscription_payment_count,
        'total_transaction_count': booking_transaction_count + subscription_payment_count,
        
        # Averages
        'avg_commission_per_booking': avg_commission_per_booking,
        'avg_subscription_payment': avg_subscription_payment,
        
        # Charts and breakdowns
        'daily_revenue': json.dumps(daily_revenue),
        'payment_method_breakdown': payment_method_breakdown,
        'top_photographers': top_photographers,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'admin_dashboard/platform_revenue.html', context)


@login_required
@user_passes_test(is_admin)
def subscription_plan_add(request):
    """Add new subscription plan"""
    from payments.models import SubscriptionPlan
    from .forms import SubscriptionPlanForm
    
    if request.method == 'POST':
        form = SubscriptionPlanForm(request.POST)
        if form.is_valid():
            plan = form.save()
            messages.success(request, f'Subscription plan "{plan.display_name}" created successfully!')
            return redirect('admin_dashboard:subscription_plans')
    else:
        form = SubscriptionPlanForm()
    
    context = {
        'form': form,
        'page_title': 'Add Subscription Plan',
        'action': 'Add',
    }
    return render(request, 'admin_dashboard/subscription_plan_form.html', context)


@login_required
@user_passes_test(is_admin)
def subscription_plan_edit(request, plan_id):
    """Edit existing subscription plan"""
    from payments.models import SubscriptionPlan
    from .forms import SubscriptionPlanForm
    
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    
    if request.method == 'POST':
        form = SubscriptionPlanForm(request.POST, instance=plan)
        if form.is_valid():
            plan = form.save()
            messages.success(request, f'Subscription plan "{plan.display_name}" updated successfully!')
            return redirect('admin_dashboard:subscription_plans')
    else:
        form = SubscriptionPlanForm(instance=plan)
    
    context = {
        'form': form,
        'plan': plan,
        'page_title': f'Edit {plan.display_name}',
        'action': 'Update',
    }
    return render(request, 'admin_dashboard/subscription_plan_form.html', context)


@login_required
@user_passes_test(is_admin)
def subscription_plan_delete(request, plan_id):
    """Delete subscription plan"""
    from payments.models import SubscriptionPlan
    
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    
    # Check if plan has active subscriptions
    if plan.usersubscription_set.filter(status__in=['active', 'trial']).exists():
        messages.error(request, f'Cannot delete "{plan.display_name}" - it has active subscriptions.')
        return redirect('admin_dashboard:subscription_plans')
    
    if request.method == 'POST':
        plan_name = plan.display_name
        plan.delete()
        messages.success(request, f'Subscription plan "{plan_name}" deleted successfully!')
        return redirect('admin_dashboard:subscription_plans')
    
    context = {
        'plan': plan,
        'page_title': f'Delete {plan.display_name}',
        'subscribers_count': plan.usersubscription_set.count(),
    }
    return render(request, 'admin_dashboard/subscription_plan_delete.html', context)
