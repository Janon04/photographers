
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
import json

from .models import Review, ReviewResponse, ReviewHelpfulness, ReviewAnalytics, ReviewCategory, ReviewComment, ReviewLikeStats
from .forms import (
    DetailedReviewForm, QuickReviewForm, ReviewResponseForm, 
    ReviewHelpfulnessForm, ReviewSearchForm, ReviewAnalyticsFilterForm,
    AnonymousReviewForm
)
from users.models import User
from bookings.models import Booking
from config.email_service import EmailService
import logging

logger = logging.getLogger(__name__)


def add_review(request):
    """Enhanced review submission with detailed ratings - supports both authenticated and anonymous users"""
    
    # For authenticated users, check completed bookings
    completed_bookings = None
    if request.user.is_authenticated:
        completed_bookings = Booking.objects.filter(
            client=request.user, 
            status='completed'
        ).exclude(review__isnull=False)
    
    # Get all photographers for anonymous users
    from users.models import User
    photographers = User.objects.filter(role='photographer', is_active=True)
    
    if request.method == 'POST':
        # Determine if this is an authenticated or anonymous review
        is_authenticated = request.user.is_authenticated
        
        if is_authenticated and completed_bookings and completed_bookings.exists():
            # Authenticated user with bookings - use detailed form
            form = DetailedReviewForm(user=request.user, data=request.POST)
        else:
            # Anonymous user or authenticated user without bookings - use anonymous form
            form = AnonymousReviewForm(data=request.POST)
        
        if form.is_valid():
            review = form.save(commit=False)
            
            # Set reviewer if authenticated
            if is_authenticated:
                review.reviewer = request.user
                if hasattr(form, 'cleaned_data') and 'booking' in form.cleaned_data and form.cleaned_data['booking']:
                    review.booking = form.cleaned_data['booking']
                    review.photographer = review.booking.photographer
                    review.is_verified = True  # Verified because it's based on actual booking
                else:
                    # Authenticated user but no booking selected
                    review.photographer_id = request.POST.get('photographer_id')
                    review.is_verified = False
            else:
                # Anonymous review
                review.reviewer = None
                review.photographer_id = request.POST.get('photographer_id')
                review.is_verified = False
                # Store anonymous reviewer info
                review.anonymous_name = request.POST.get('anonymous_name', 'Anonymous')
                review.anonymous_email = request.POST.get('anonymous_email', '')
            
            review.save()
            
            # Save many-to-many relationships
            if hasattr(form, 'cleaned_data') and 'categories' in form.cleaned_data:
                review.categories.set(form.cleaned_data['categories'])
            
            # Send email notification to photographer
            try:
                EmailService.send_review_notification(review)
            except Exception as e:
                logger.error(f"Failed to send review notification: {str(e)}")
            
            # Update photographer analytics
            analytics, created = ReviewAnalytics.objects.get_or_create(
                photographer=review.photographer
            )
            analytics.update_analytics()
            
            success_msg = 'Your review has been submitted successfully!'
            if not is_authenticated or not review.is_verified:
                success_msg += ' It will be reviewed before being published.'
            
            messages.success(request, success_msg)
            
            reviewer_info = request.user.email if is_authenticated else f"anonymous user ({review.anonymous_email})"
            logger.info(f"New review added by {reviewer_info} for photographer {review.photographer.email}")
            
            return redirect('reviews:review_detail', review_id=review.id)
    else:
        # Initialize appropriate form based on user authentication
        if request.user.is_authenticated and completed_bookings and completed_bookings.exists():
            form = DetailedReviewForm(user=request.user)
        else:
            form = AnonymousReviewForm()
    
    context = {
        'form': form,
        'completed_bookings': completed_bookings,
        'photographers': photographers,
        'is_authenticated': request.user.is_authenticated,
        'quick_review_bookings': completed_bookings[:3] if completed_bookings else None
    }
    return render(request, 'reviews/add_review.html', context)


def reviews_list(request):
    """Enhanced reviews list with filtering and search"""
    
    # Initialize the search form with GET parameters or empty
    search_form = ReviewSearchForm(request.GET or None)
    
    reviews = Review.objects.filter(is_approved=True).select_related(
        'reviewer', 'photographer', 'booking'
    ).prefetch_related('categories')
    
    # Apply filters
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search_query', '').strip()
        if search_query:
            reviews = reviews.filter(
                Q(title__icontains=search_query) |
                Q(comment__icontains=search_query) |
                Q(photographer__first_name__icontains=search_query) |
                Q(photographer__last_name__icontains=search_query)
            )
        
        rating_filter = search_form.cleaned_data.get('rating_filter', '').strip()
        if rating_filter:
            try:
                reviews = reviews.filter(overall_rating__gte=int(rating_filter))
            except (ValueError, TypeError):
                pass  # Ignore invalid rating values
        
        sentiment_filter = search_form.cleaned_data.get('sentiment_filter', '').strip()
        if sentiment_filter:
            reviews = reviews.filter(ai_sentiment=sentiment_filter)
        
        photographer = search_form.cleaned_data.get('photographer', '').strip()
        if photographer:
            try:
                reviews = reviews.filter(photographer__id=int(photographer))
            except (ValueError, TypeError):
                pass  # Ignore invalid photographer ID
        
        sort_by = search_form.cleaned_data.get('sort_by', '-created_at').strip()
        if sort_by:
            reviews = reviews.order_by(sort_by)
        else:
            reviews = reviews.order_by('-created_at')
    else:
        reviews = reviews.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(reviews, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get featured reviews
    featured_reviews = Review.objects.filter(
        is_approved=True, is_featured=True
    ).select_related('reviewer', 'photographer')[:3]
    
    # Get statistics
    stats = {
        'total_reviews': Review.objects.filter(is_approved=True).count(),
        'average_rating': Review.objects.filter(is_approved=True).aggregate(
            avg=Avg('overall_rating')
        )['avg'] or 0,
        'recent_reviews': Review.objects.filter(
            is_approved=True,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
    }
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'featured_reviews': featured_reviews,
        'stats': stats,
        'categories': ReviewCategory.objects.filter(is_active=True)
    }
    return render(request, 'reviews/reviews_list.html', context)


def review_detail(request, review_id):
    """Detailed view of a single review"""
    
    try:
        review = get_object_or_404(
            Review.objects.select_related('reviewer', 'photographer', 'booking'),
            id=review_id,
            is_approved=True
        )
    except:
        # Redirect to reviews list with helpful message for non-existent reviews
        messages.error(request, f'Review #{review_id} not found. Here are all available reviews.')
        return redirect('reviews:reviews_list')
    
    # Check if user can vote on helpfulness
    can_vote = request.user.is_authenticated and request.user != review.reviewer
    user_vote = None
    
    if can_vote:
        try:
            user_vote = ReviewHelpfulness.objects.get(review=review, user=request.user)
        except ReviewHelpfulness.DoesNotExist:
            pass
    
    # Get photographer's other reviews
    other_reviews = Review.objects.filter(
        photographer=review.photographer,
        is_approved=True
    ).exclude(id=review.id).order_by('-created_at')[:5]
    
    context = {
        'review': review,
        'can_vote': can_vote,
        'user_vote': user_vote,
        'other_reviews': other_reviews,
        'sentiment_analysis': review.sentiment_analysis,
        'response_form': ReviewResponseForm() if request.user == review.photographer else None
    }
    return render(request, 'reviews/review_detail.html', context)


@login_required
@require_POST
def vote_helpfulness(request, review_id):
    """AJAX endpoint for voting on review helpfulness"""
    
    review = get_object_or_404(Review, id=review_id)
    is_helpful = request.POST.get('is_helpful') == 'true'
    
    if request.user == review.reviewer:
        return JsonResponse({'error': 'You cannot vote on your own review'}, status=400)
    
    vote, created = ReviewHelpfulness.objects.get_or_create(
        review=review,
        user=request.user,
        defaults={'is_helpful': is_helpful}
    )
    
    if not created:
        # Update existing vote
        vote.is_helpful = is_helpful
        vote.save()
    
    # Update review helpfulness counts
    helpfulness_votes = ReviewHelpfulness.objects.filter(review=review)
    helpful_count = helpfulness_votes.filter(is_helpful=True).count()
    total_count = helpfulness_votes.count()
    
    review.helpfulness_votes = helpful_count
    review.total_votes = total_count
    review.save(update_fields=['helpfulness_votes', 'total_votes'])
    
    return JsonResponse({
        'helpful_count': helpful_count,
        'total_count': total_count,
        'percentage': review.get_helpfulness_percentage()
    })


@login_required
def add_response(request, review_id):
    """Add photographer response to a review"""
    
    review = get_object_or_404(Review, id=review_id)
    
    # Only the photographer can respond to their reviews
    if request.user != review.photographer:
        messages.error(request, 'You can only respond to your own reviews.')
        return redirect('reviews:review_detail', review_id=review_id)
    
    if request.method == 'POST':
        form = ReviewResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.review = review
            response.save()
            
            messages.success(request, 'Your response has been added successfully!')
            
            # Update analytics
            analytics, created = ReviewAnalytics.objects.get_or_create(
                photographer=request.user
            )
            analytics.update_analytics()
            
            return redirect('reviews:review_detail', review_id=review_id)
    
    return redirect('reviews:review_detail', review_id=review_id)


@login_required
def photographer_reviews(request, photographer_id):
    """List all reviews for a specific photographer"""
    
    photographer = get_object_or_404(User, id=photographer_id)
    
    reviews = Review.objects.filter(
        photographer=photographer,
        is_approved=True
    ).select_related('reviewer').order_by('-created_at')
    
    # Get analytics
    analytics, created = ReviewAnalytics.objects.get_or_create(
        photographer=photographer
    )
    if created:
        analytics.update_analytics()
    
    # Pagination
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'photographer': photographer,
        'page_obj': page_obj,
        'analytics': analytics,
        'sentiment_distribution': analytics.get_sentiment_distribution()
    }
    return render(request, 'reviews/photographer_reviews.html', context)


@login_required
def sentiment_report(request):
    """Comprehensive sentiment analysis report for photographers"""
    
    # Only photographers can access their sentiment reports
    if not hasattr(request.user, 'role') or request.user.role != 'photographer':
        messages.error(request, 'Only photographers can access sentiment reports.')
        return redirect('reviews:reviews_list')
    
    filter_form = ReviewAnalyticsFilterForm(request.GET)
    
    # Get reviews for the current photographer
    reviews = Review.objects.filter(photographer=request.user, is_approved=True)
    
    # Apply time filter
    if filter_form.is_valid():
        period = filter_form.cleaned_data.get('period', '30')
        include_unverified = filter_form.cleaned_data.get('include_unverified', False)
        
        if not include_unverified:
            reviews = reviews.filter(is_verified=True)
        
        if period != 'all':
            days = int(period)
            reviews = reviews.filter(
                created_at__gte=timezone.now() - timedelta(days=days)
            )
    
    # Get analytics
    analytics, created = ReviewAnalytics.objects.get_or_create(
        photographer=request.user
    )
    if created or analytics.last_calculated < timezone.now() - timedelta(hours=1):
        analytics.update_analytics()
    
    # Calculate detailed statistics
    total_reviews = reviews.count()
    
    if total_reviews > 0:
        # Rating statistics
        rating_stats = reviews.aggregate(
            avg_overall=Avg('overall_rating'),
            avg_quality=Avg('quality_rating'),
            avg_professionalism=Avg('professionalism_rating'),
            avg_communication=Avg('communication_rating'),
            avg_value=Avg('value_rating')
        )
        
        # Sentiment analysis
        sentiment_counts = reviews.values('ai_sentiment').annotate(
            count=Count('id')
        ).order_by('ai_sentiment')
        
        # Recent trends
        recent_reviews = reviews.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        # Key phrases analysis
        all_key_phrases = []
        for review in reviews.exclude(key_phrases=[]):
            all_key_phrases.extend(review.key_phrases)
        
        # Count phrase frequency
        phrase_frequency = {}
        for phrase in all_key_phrases:
            phrase_frequency[phrase] = phrase_frequency.get(phrase, 0) + 1
        
        top_phrases = sorted(
            phrase_frequency.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Reviews needing attention
        attention_reviews = reviews.filter(
            models.Q(ai_sentiment='negative') |
            models.Q(overall_rating__lte=2) |
            models.Q(rating_consistency=False)
        ).order_by('-created_at')[:5]
        
        sentiment_data = {
            'total_reviews': total_reviews,
            'rating_stats': rating_stats,
            'sentiment_counts': list(sentiment_counts),
            'sentiment_distribution': analytics.get_sentiment_distribution(),
            'recent_trend': analytics.rating_trend,
            'top_phrases': top_phrases,
            'attention_reviews': attention_reviews,
            'response_rate': analytics.response_rate
        }
    else:
        sentiment_data = {
            'total_reviews': 0,
            'rating_stats': {},
            'sentiment_counts': [],
            'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
            'recent_trend': 'stable',
            'top_phrases': [],
            'attention_reviews': [],
            'response_rate': 0
        }
    
    context = {
        'sentiment_data': sentiment_data,
        'analytics': analytics,
        'filter_form': filter_form,
        'recent_reviews': reviews.order_by('-created_at')[:10]
    }
    
    return render(request, 'reviews/sentiment_report.html', context)


@login_required
def analytics_dashboard(request):
    """Advanced analytics dashboard for photographers"""
    
    if not hasattr(request.user, 'role') or request.user.role != 'photographer':
        messages.error(request, 'Only photographers can access analytics.')
        return redirect('reviews:reviews_list')
    
    # Get or create analytics
    analytics, created = ReviewAnalytics.objects.get_or_create(
        photographer=request.user
    )
    if created:
        analytics.update_analytics()
    
    # Get detailed review data for charts
    reviews = Review.objects.filter(
        photographer=request.user,
        is_approved=True
    ).order_by('-created_at')
    
    # Monthly review trends
    monthly_data = []
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=31)
        
        month_reviews = reviews.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        )
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'count': month_reviews.count(),
            'avg_rating': month_reviews.aggregate(avg=Avg('overall_rating'))['avg'] or 0,
            'positive_sentiment': month_reviews.filter(ai_sentiment='positive').count()
        })
    
    monthly_data.reverse()
    
    context = {
        'analytics': analytics,
        'monthly_data': json.dumps(monthly_data),
        'total_reviews': reviews.count(),
        'recent_reviews': reviews[:5],
        'categories_performance': ReviewCategory.objects.filter(
            review__photographer=request.user,
            is_active=True
        ).annotate(
            review_count=Count('review'),
            avg_rating=Avg('review__overall_rating')
        ).order_by('-review_count')[:5]
    }
    
    return render(request, 'reviews/analytics_dashboard.html', context)


def public_analytics(request, photographer_id):
    """Public analytics view for potential clients"""
    
    photographer = get_object_or_404(User, id=photographer_id)
    
    analytics, created = ReviewAnalytics.objects.get_or_create(
        photographer=photographer
    )
    if created:
        analytics.update_analytics()
    
    # Get recent approved reviews
    recent_reviews = Review.objects.filter(
        photographer=photographer,
        is_approved=True
    ).order_by('-created_at')[:6]
    
    # Get category performance
    category_performance = ReviewCategory.objects.filter(
        review__photographer=photographer,
        review__is_approved=True,
        is_active=True
    ).annotate(
        review_count=Count('review'),
        avg_rating=Avg('review__overall_rating')
    ).order_by('-avg_rating')[:5]
    
    context = {
        'photographer': photographer,
        'analytics': analytics,
        'recent_reviews': recent_reviews,
        'category_performance': category_performance,
        'sentiment_distribution': analytics.get_sentiment_distribution()
    }
    
    return render(request, 'reviews/public_analytics.html', context)


# Enhanced Like/Dislike and Comment System

@require_POST
def toggle_review_like(request, review_id):
    """AJAX endpoint for toggling review likes"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        review = get_object_or_404(Review, id=review_id, is_approved=True)
        
        # Users cannot like their own reviews
        if request.user == review.reviewer:
            return JsonResponse({'error': 'Cannot like your own review'}, status=400)
        
        review.toggle_like(request.user)
        
        return JsonResponse({
            'success': True,
            'like_count': review.get_like_count(),
            'dislike_count': review.get_dislike_count(),
            'user_vote': review.get_user_vote(request.user)
        })
        
    except Exception as e:
        logger.error(f"Error toggling like for review {review_id}: {str(e)}")
        return JsonResponse({'error': 'Something went wrong'}, status=500)


@require_POST
def toggle_review_dislike(request, review_id):
    """AJAX endpoint for toggling review dislikes"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        review = get_object_or_404(Review, id=review_id, is_approved=True)
        
        # Users cannot dislike their own reviews
        if request.user == review.reviewer:
            return JsonResponse({'error': 'Cannot dislike your own review'}, status=400)
        
        review.toggle_dislike(request.user)
        
        return JsonResponse({
            'success': True,
            'like_count': review.get_like_count(),
            'dislike_count': review.get_dislike_count(),
            'user_vote': review.get_user_vote(request.user)
        })
        
    except Exception as e:
        logger.error(f"Error toggling dislike for review {review_id}: {str(e)}")
        return JsonResponse({'error': 'Something went wrong'}, status=500)


@require_POST
def add_review_comment(request, review_id):
    """AJAX endpoint for adding comments to reviews"""
    try:
        review = get_object_or_404(Review, id=review_id, is_approved=True)
        comment_text = request.POST.get('comment_text', '').strip()
        parent_comment_id = request.POST.get('parent_comment_id')
        
        if not comment_text:
            return JsonResponse({'error': 'Comment text is required'}, status=400)
        
        if len(comment_text) < 5:
            return JsonResponse({'error': 'Comment must be at least 5 characters'}, status=400)
        
        if len(comment_text) > 500:
            return JsonResponse({'error': 'Comment must be less than 500 characters'}, status=400)
        
        parent_comment = None
        if parent_comment_id:
            try:
                parent_comment = ReviewComment.objects.get(id=parent_comment_id, review=review)
            except ReviewComment.DoesNotExist:
                return JsonResponse({'error': 'Parent comment not found'}, status=400)
        
        # Handle anonymous vs authenticated users
        if request.user.is_authenticated:
            comment = review.add_comment(
                user=request.user,
                comment_text=comment_text,
                parent_comment=parent_comment
            )
        else:
            # Anonymous comment
            anonymous_name = request.POST.get('anonymous_name', '').strip()
            anonymous_email = request.POST.get('anonymous_email', '').strip()
            
            if not anonymous_name:
                return JsonResponse({'error': 'Name is required for anonymous comments'}, status=400)
            
            comment = review.add_comment(
                user=None,
                comment_text=comment_text,
                parent_comment=parent_comment,
                anonymous_name=anonymous_name,
                anonymous_email=anonymous_email
            )
        
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'commenter_name': comment.commenter_display_name,
                'comment_text': comment.comment_text,
                'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p'),
                'is_anonymous': comment.is_anonymous,
                'parent_comment_id': comment.parent_comment.id if comment.parent_comment else None
            },
            'comment_count': review.get_comment_count()
        })
        
    except Exception as e:
        logger.error(f"Error adding comment to review {review_id}: {str(e)}")
        return JsonResponse({'error': 'Something went wrong'}, status=500)


def get_review_comments(request, review_id):
    """Get all comments for a review"""
    try:
        review = get_object_or_404(Review, id=review_id, is_approved=True)
        comments = ReviewComment.objects.filter(
            review=review, 
            is_approved=True,
            parent_comment__isnull=True  # Only top-level comments
        ).select_related('commenter').prefetch_related('replies').order_by('created_at')
        
        comments_data = []
        for comment in comments:
            comment_data = {
                'id': comment.id,
                'commenter_name': comment.commenter_display_name,
                'comment_text': comment.comment_text,
                'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p'),
                'is_anonymous': comment.is_anonymous,
                'replies': []
            }
            
            # Add replies
            for reply in comment.replies.filter(is_approved=True).order_by('created_at'):
                reply_data = {
                    'id': reply.id,
                    'commenter_name': reply.commenter_display_name,
                    'comment_text': reply.comment_text,
                    'created_at': reply.created_at.strftime('%B %d, %Y at %I:%M %p'),
                    'is_anonymous': reply.is_anonymous,
                }
                comment_data['replies'].append(reply_data)
            
            comments_data.append(comment_data)
        
        return JsonResponse({
            'success': True,
            'comments': comments_data,
            'comment_count': review.get_comment_count()
        })
        
    except Exception as e:
        logger.error(f"Error getting comments for review {review_id}: {str(e)}")
        return JsonResponse({'error': 'Something went wrong'}, status=500)
