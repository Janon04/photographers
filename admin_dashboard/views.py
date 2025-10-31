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

User = get_user_model()

def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and user.role == User.Roles.ADMIN

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
    # Get current date for analytics
    today = timezone.now().date()
    
    # Basic stats
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
    last_30_days = today - timedelta(days=30)
    new_users_30d = User.objects.filter(date_joined__gte=last_30_days).count()
    new_bookings_30d = Booking.objects.filter(created_at__gte=last_30_days).count()
    
    # User growth chart data (last 7 days)
    user_growth = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = User.objects.filter(date_joined__date=date).count()
        user_growth.append({
            'date': date.strftime('%m/%d'),
            'count': count
        })
    
    # Booking status distribution
    booking_stats = {
        'pending': Booking.objects.filter(status='pending').count(),
        'confirmed': Booking.objects.filter(status='confirmed').count(),
        'completed': Booking.objects.filter(status='completed').count(),
        'cancelled': Booking.objects.filter(status='cancelled').count(),
    }
    
    # Recent activities
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_bookings = Booking.objects.order_by('-created_at')[:5]
    recent_reviews = Review.objects.order_by('-created_at')[:5]
    
    # Pending approvals
    pending_reviews = Review.objects.filter(is_approved=False).count()
    total_contact_messages = ContactMessage.objects.count()
    
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
        'total_contact_messages': total_contact_messages,
    }
    
    return render(request, 'admin_dashboard/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def users_management(request):
    """Manage all users"""
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    is_verified_filter = request.GET.get('verified', '')
    
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
def bookings_management(request):
    """Manage all bookings"""
    status_filter = request.GET.get('status', '')
    payment_filter = request.GET.get('payment', '')
    search_query = request.GET.get('search', '')
    
    bookings = Booking.objects.select_related('client', 'photographer')
    
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
        'booking_statuses': Booking.STATUS_CHOICES,
        'payment_statuses': Booking.PAYMENT_STATUS_CHOICES,
    }
    
    return render(request, 'admin_dashboard/bookings_management.html', context)

@login_required
@user_passes_test(is_admin)
def reviews_management(request):
    """Manage all reviews"""
    approval_filter = request.GET.get('approved', '')
    search_query = request.GET.get('search', '')
    
    reviews = Review.objects.select_related('reviewer', 'photographer', 'booking')
    
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
    log_admin_activity(
        request.user, action, 'Review', review.id,
        f"Review by {review.reviewer.email}", f"{'Approved' if review.is_approved else 'Rejected'} review",
        request.META.get('REMOTE_ADDR')
    )
    
    status = 'approved' if review.is_approved else 'rejected'
    messages.success(request, f'Review has been {status}.')
    
    return JsonResponse({'success': True, 'is_approved': review.is_approved})

@login_required
@user_passes_test(is_admin)
def analytics_dashboard(request):
    """Advanced analytics dashboard"""
    # Time period filter
    period = request.GET.get('period', '30')  # days
    try:
        days = int(period)
    except (ValueError, TypeError):
        days = 30
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # User registration trends
    user_registrations = []
    photographer_registrations = []
    client_registrations = []
    
    for i in range(days, -1, -1):
        date = end_date - timedelta(days=i)
        users_count = User.objects.filter(date_joined__date=date).count()
        photographers_count = User.objects.filter(
            date_joined__date=date, role=User.Roles.PHOTOGRAPHER
        ).count()
        clients_count = User.objects.filter(
            date_joined__date=date, role=User.Roles.CLIENT
        ).count()
        
        user_registrations.append({'date': date.strftime('%m/%d'), 'count': users_count})
        photographer_registrations.append({'date': date.strftime('%m/%d'), 'count': photographers_count})
        client_registrations.append({'date': date.strftime('%m/%d'), 'count': clients_count})
    
    # Booking trends
    booking_trends = []
    revenue_trends = []
    
    for i in range(days, -1, -1):
        date = end_date - timedelta(days=i)
        bookings_count = Booking.objects.filter(created_at__date=date).count()
        revenue = Transaction.objects.filter(
            created_at__date=date, status='paid'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        booking_trends.append({'date': date.strftime('%m/%d'), 'count': bookings_count})
        revenue_trends.append({'date': date.strftime('%m/%d'), 'amount': float(revenue)})
    
    # Top photographers by bookings
    top_photographers = User.objects.filter(
        role=User.Roles.PHOTOGRAPHER
    ).annotate(
        booking_count=Count('photographer_bookings'),
        completed_bookings=Count(
            'photographer_bookings',
            filter=Q(photographer_bookings__status='completed')
        )
    ).order_by('-booking_count')[:10]
    
    # Service type popularity
    service_popularity = Booking.objects.values('service_type').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Calculate totals and period metrics
    total_users = User.objects.count()
    total_photographers = User.objects.filter(role=User.Roles.PHOTOGRAPHER).count()
    total_bookings = Booking.objects.count()
    total_revenue = Transaction.objects.filter(status='paid').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Period-specific metrics
    new_users = User.objects.filter(date_joined__gte=start_date).count()
    new_photographers = User.objects.filter(
        date_joined__gte=start_date, role=User.Roles.PHOTOGRAPHER
    ).count()
    new_bookings = Booking.objects.filter(created_at__gte=start_date).count()
    period_revenue = Transaction.objects.filter(
        created_at__gte=start_date, status='paid'
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
    }
    
    return render(request, 'admin_dashboard/analytics.html', context)

@login_required
@user_passes_test(is_admin)
def notifications_management(request):
    """Manage system notifications"""
    if request.method == 'POST':
        form = SystemNotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.created_by = request.user
            notification.save()
            
            log_admin_activity(
                request.user, 'create', 'SystemNotification', notification.id,
                f"Notification: {notification.title}", f"Created system notification",
                request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, 'System notification created successfully.')
            return redirect('admin_dashboard:notifications_management')
    else:
        form = SystemNotificationForm()
    
    notifications = SystemNotification.objects.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
    }
    
    return render(request, 'admin_dashboard/notifications.html', context)

@login_required
@user_passes_test(is_admin)
def activity_logs(request):
    """View admin activity logs"""
    admin_filter = request.GET.get('admin', '')
    action_filter = request.GET.get('action', '')
    model_filter = request.GET.get('model', '')
    
    logs = AdminActivityLog.objects.select_related('admin_user')
    
    if admin_filter:
        logs = logs.filter(admin_user__email__icontains=admin_filter)
        
    if action_filter:
        logs = logs.filter(action=action_filter)
        
    if model_filter:
        logs = logs.filter(target_model__icontains=model_filter)
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'admin_filter': admin_filter,
        'action_filter': action_filter,
        'model_filter': model_filter,
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
