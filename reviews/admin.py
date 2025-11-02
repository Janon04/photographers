from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Avg
from .models import Review, ReviewCategory, ReviewResponse, ReviewHelpfulness, ReviewAnalytics


@admin.register(ReviewCategory)
class ReviewCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'review_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    
    def review_count(self, obj):
        return obj.review_set.count()
    review_count.short_description = 'Reviews'


class ReviewResponseInline(admin.StackedInline):
    model = ReviewResponse
    extra = 0
    fields = ('response_text', 'is_public', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'reviewer_name', 'photographer_name', 'overall_rating', 
        'ai_sentiment_display', 'is_approved', 'is_featured', 
        'created_at', 'helpfulness_score'
    )
    list_filter = (
        'is_approved', 'is_featured', 'ai_sentiment', 
        'overall_rating', 'created_at', 'is_verified'
    )
    search_fields = (
        'reviewer__first_name', 'reviewer__last_name', 'reviewer__email',
        'photographer__first_name', 'photographer__last_name', 'photographer__email',
        'title', 'comment'
    )
    list_editable = ('is_approved', 'is_featured')
    readonly_fields = (
        'created_at', 'updated_at', 'word_count', 'reading_time_seconds',
        'ai_sentiment', 'sentiment_confidence', 'analysis_status',
        'sentiment_analysis_display', 'key_phrases_display'
    )
    fieldsets = (
        ('Basic Information', {
            'fields': ('booking', 'reviewer', 'photographer', 'title')
        }),
        ('Ratings', {
            'fields': (
                'overall_rating', 'quality_rating', 'professionalism_rating',
                'communication_rating', 'value_rating'
            )
        }),
        ('Review Content', {
            'fields': ('comment', 'categories')
        }),
        ('Status & Settings', {
            'fields': ('is_approved', 'is_featured', 'is_verified')
        }),
        ('Analytics', {
            'fields': (
                'word_count', 'reading_time_seconds', 'helpfulness_votes',
                'total_votes', 'ai_sentiment', 'sentiment_confidence',
                'analysis_status', 'sentiment_analysis_display', 'key_phrases_display'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    inlines = [ReviewResponseInline]
    actions = ['approve_reviews', 'feature_reviews', 'run_sentiment_analysis']
    
    def reviewer_name(self, obj):
        if obj.reviewer:
            return obj.reviewer.get_full_name() or obj.reviewer.username
        else:
            return obj.anonymous_name or 'Anonymous'
    reviewer_name.short_description = 'Reviewer'
    
    def photographer_name(self, obj):
        return obj.photographer.get_full_name() or obj.photographer.username
    photographer_name.short_description = 'Photographer'
    
    def ai_sentiment_display(self, obj):
        colors = {
            'positive': '#4CAF50',
            'negative': '#F44336',
            'neutral': '#FF9800',
            'mixed': '#9C27B0'
        }
        color = colors.get(obj.ai_sentiment, '#9E9E9E')
        confidence = f" ({obj.sentiment_confidence:.1%})" if obj.sentiment_confidence else ""
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{}</span>',
            color,
            obj.ai_sentiment.title(),
            confidence
        )
    ai_sentiment_display.short_description = 'AI Sentiment'
    
    def helpfulness_score(self, obj):
        if obj.total_votes == 0:
            return "No votes"
        percentage = (obj.helpfulness_votes / obj.total_votes) * 100
        return f"{obj.helpfulness_votes}/{obj.total_votes} ({percentage:.1f}%)"
    helpfulness_score.short_description = 'Helpfulness'
    
    def sentiment_analysis_display(self, obj):
        if not obj.sentiment_analysis:
            return "No analysis available"
        
        analysis = obj.sentiment_analysis
        html = "<div style='max-width: 400px;'>"
        
        if 'emotions' in analysis:
            html += "<strong>Emotions:</strong><br>"
            for emotion, score in analysis['emotions'].items():
                html += f"• {emotion.title()}: {score:.2f}<br>"
        
        if 'suggestions' in analysis:
            html += "<br><strong>Suggestions:</strong><br>"
            for suggestion in analysis['suggestions'][:3]:
                html += f"• {suggestion}<br>"
        
        html += "</div>"
        return format_html(html)
    sentiment_analysis_display.short_description = 'Sentiment Analysis'
    
    def key_phrases_display(self, obj):
        if not obj.key_phrases:
            return "None"
        phrases = obj.key_phrases[:5]  # Show first 5 phrases
        return ", ".join(f'"{phrase}"' for phrase in phrases)
    key_phrases_display.short_description = 'Key Phrases'
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} reviews approved successfully.')
    approve_reviews.short_description = "Approve selected reviews"
    
    def feature_reviews(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} reviews featured successfully.')
    feature_reviews.short_description = "Feature selected reviews"
    
    def run_sentiment_analysis(self, request, queryset):
        count = 0
        for review in queryset:
            try:
                review.analyze_sentiment()
                count += 1
            except Exception as e:
                self.message_user(request, f'Error analyzing review {review.id}: {str(e)}', level='ERROR')
        
        if count > 0:
            self.message_user(request, f'Sentiment analysis completed for {count} reviews.')
    run_sentiment_analysis.short_description = "Run sentiment analysis"


@admin.register(ReviewResponse)
class ReviewResponseAdmin(admin.ModelAdmin):
    list_display = ('review_summary', 'photographer', 'is_public', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('review__reviewer__first_name', 'review__photographer__first_name', 'response_text')
    readonly_fields = ('created_at', 'updated_at')
    
    def review_summary(self, obj):
        reviewer_name = obj.review.reviewer.get_full_name() if obj.review.reviewer else obj.review.anonymous_name or 'Anonymous'
        return f"Response to {reviewer_name}'s review"
    review_summary.short_description = 'Review'
    
    def photographer(self, obj):
        return obj.review.photographer.get_full_name()
    photographer.short_description = 'Photographer'


@admin.register(ReviewHelpfulness)
class ReviewHelpfulnessAdmin(admin.ModelAdmin):
    list_display = ('user', 'review_summary', 'is_helpful', 'created_at')
    list_filter = ('is_helpful', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'review__title')
    readonly_fields = ('created_at',)
    
    def review_summary(self, obj):
        reviewer_name = obj.review.reviewer.get_full_name() if obj.review.reviewer else obj.review.anonymous_name or 'Anonymous'
        return f"{obj.review.title or 'Untitled'} by {reviewer_name}"
    review_summary.short_description = 'Review'


@admin.register(ReviewAnalytics)
class ReviewAnalyticsAdmin(admin.ModelAdmin):
    list_display = (
        'photographer', 'total_reviews', 'average_overall_rating',
        'sentiment_summary', 'response_rate', 'last_calculated'
    )
    list_filter = ('rating_trend', 'sentiment_trend', 'last_calculated')
    search_fields = ('photographer__first_name', 'photographer__last_name', 'photographer__email')
    readonly_fields = (
        'total_reviews', 'average_overall_rating', 'average_quality_rating',
        'average_professionalism_rating', 'average_communication_rating',
        'average_value_rating', 'positive_sentiment_count', 'negative_sentiment_count',
        'neutral_sentiment_count', 'total_helpfulness_votes', 'response_rate',
        'rating_trend', 'sentiment_trend', 'last_calculated'
    )
    actions = ['recalculate_analytics']
    
    fieldsets = (
        ('Photographer', {
            'fields': ('photographer',)
        }),
        ('Rating Statistics', {
            'fields': (
                'total_reviews', 'average_overall_rating', 'average_quality_rating',
                'average_professionalism_rating', 'average_communication_rating',
                'average_value_rating'
            )
        }),
        ('Sentiment Statistics', {
            'fields': (
                'positive_sentiment_count', 'negative_sentiment_count',
                'neutral_sentiment_count'
            )
        }),
        ('Engagement Statistics', {
            'fields': ('total_helpfulness_votes', 'response_rate')
        }),
        ('Trends', {
            'fields': ('rating_trend', 'sentiment_trend')
        }),
        ('Last Updated', {
            'fields': ('last_calculated',)
        })
    )
    
    def sentiment_summary(self, obj):
        total_sentiment = obj.positive_sentiment_count + obj.negative_sentiment_count + obj.neutral_sentiment_count
        if total_sentiment == 0:
            return "No data"
        
        pos_pct = (obj.positive_sentiment_count / total_sentiment) * 100
        neg_pct = (obj.negative_sentiment_count / total_sentiment) * 100
        
        return format_html(
            '<span style="color: #4CAF50;">{}%</span> / '
            '<span style="color: #F44336;">{}%</span> positive/negative',
            int(pos_pct), int(neg_pct)
        )
    sentiment_summary.short_description = 'Sentiment Split'
    
    def recalculate_analytics(self, request, queryset):
        count = 0
        for analytics in queryset:
            try:
                analytics.update_analytics()
                count += 1
            except Exception as e:
                self.message_user(request, f'Error updating analytics for {analytics.photographer}: {str(e)}', level='ERROR')
        
        if count > 0:
            self.message_user(request, f'Analytics recalculated for {count} photographers.')
    recalculate_analytics.short_description = "Recalculate analytics"


# Custom admin site configuration
admin.site.site_header = "Photography Platform Administration"
admin.site.site_title = "Photography Platform Admin"
admin.site.index_title = "Welcome to Photography Platform Administration"
