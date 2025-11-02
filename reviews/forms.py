# Enhanced Review forms with comprehensive rating system
from django import forms
from django.core.validators import MinLengthValidator
from .models import Review, ReviewResponse, ReviewHelpfulness, ReviewCategory
from bookings.models import Booking


class DetailedReviewForm(forms.ModelForm):
    """Comprehensive review form with detailed ratings"""
    
    booking = forms.ModelChoiceField(
        queryset=Booking.objects.none(),
        label='Select Booking to Review',
        help_text='Choose the completed booking you want to review.',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    title = forms.CharField(
        max_length=200,
        label='Review Title',
        help_text='Brief summary of your experience',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., "Excellent wedding photography service"',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    # Star ratings with custom widgets
    overall_rating = forms.IntegerField(
        min_value=1, max_value=5,
        label='Overall Rating',
        widget=forms.NumberInput(attrs={
            'class': 'form-control star-rating',
            'data-rating': 'overall',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    quality_rating = forms.IntegerField(
        min_value=1, max_value=5,
        label='Photo Quality',
        widget=forms.NumberInput(attrs={
            'class': 'form-control star-rating',
            'data-rating': 'quality',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    professionalism_rating = forms.IntegerField(
        min_value=1, max_value=5,
        label='Professionalism',
        widget=forms.NumberInput(attrs={
            'class': 'form-control star-rating',
            'data-rating': 'professionalism',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    communication_rating = forms.IntegerField(
        min_value=1, max_value=5,
        label='Communication',
        widget=forms.NumberInput(attrs={
            'class': 'form-control star-rating',
            'data-rating': 'communication',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    value_rating = forms.IntegerField(
        min_value=1, max_value=5,
        label='Value for Money',
        widget=forms.NumberInput(attrs={
            'class': 'form-control star-rating',
            'data-rating': 'value',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    comment = forms.CharField(
        validators=[MinLengthValidator(20, 'Please provide at least 20 characters in your review.')],
        label='Detailed Review',
        help_text='Share your detailed experience (minimum 20 characters)',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Tell others about your experience with this photographer...',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    categories = forms.ModelMultipleChoiceField(
        queryset=ReviewCategory.objects.filter(is_active=True),
        required=False,
        label='Review Categories',
        help_text='Select relevant categories (optional)',
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        })
    )

    class Meta:
        model = Review
        fields = [
            'booking', 'title', 'overall_rating', 'quality_rating', 
            'professionalism_rating', 'communication_rating', 'value_rating',
            'comment', 'categories'
        ]

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Filter bookings for the current user
            self.fields['booking'].queryset = Booking.objects.filter(
                client=user, 
                status='completed'
            ).exclude(
                review__isnull=False
            ).select_related('photographer')

    def clean(self):
        cleaned_data = super().clean()
        booking = cleaned_data.get('booking')
        
        if booking and hasattr(booking, 'review'):
            raise forms.ValidationError('This booking has already been reviewed.')
        
        # Validate ratings consistency
        overall = cleaned_data.get('overall_rating')
        detailed_ratings = [
            cleaned_data.get('quality_rating'),
            cleaned_data.get('professionalism_rating'),
            cleaned_data.get('communication_rating'),
            cleaned_data.get('value_rating')
        ]
        
        if all(detailed_ratings) and overall:
            avg_detailed = sum(detailed_ratings) / len(detailed_ratings)
            if abs(overall - avg_detailed) > 1.5:
                self.add_error('overall_rating', 
                    'Overall rating should be reasonably consistent with your detailed ratings.')
        
        return cleaned_data


class QuickReviewForm(forms.ModelForm):
    """Simplified review form for quick feedback"""
    
    overall_rating = forms.IntegerField(
        min_value=1, max_value=5,
        label='Rating',
        widget=forms.NumberInput(attrs={
            'class': 'form-control star-rating-simple',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    comment = forms.CharField(
        validators=[MinLengthValidator(10, 'Please provide at least 10 characters.')],
        label='Quick Review',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Share your quick thoughts...',
            'style': 'margin-bottom: 1rem;'
        })
    )

    class Meta:
        model = Review
        fields = ['overall_rating', 'comment']

    def save(self, commit=True):
        review = super().save(commit=False)
        # Set all detailed ratings to overall rating for quick reviews
        review.quality_rating = review.overall_rating
        review.professionalism_rating = review.overall_rating
        review.communication_rating = review.overall_rating
        review.value_rating = review.overall_rating
        review.title = f"{review.overall_rating}-star review"
        
        if commit:
            review.save()
        return review


class ReviewResponseForm(forms.ModelForm):
    """Form for photographer responses to reviews"""
    
    response_text = forms.CharField(
        validators=[MinLengthValidator(10, 'Please provide at least 10 characters.')],
        label='Your Response',
        help_text='Respond professionally to this review',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Thank you for your review...',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    is_public = forms.BooleanField(
        required=False,
        initial=True,
        label='Make response public',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    class Meta:
        model = ReviewResponse
        fields = ['response_text', 'is_public']


class ReviewHelpfulnessForm(forms.ModelForm):
    """Form for rating review helpfulness"""
    
    is_helpful = forms.BooleanField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = ReviewHelpfulness
        fields = ['is_helpful']


class ReviewSearchForm(forms.Form):
    """Form for searching and filtering reviews"""
    
    RATING_CHOICES = [
        ('', 'All Ratings'),
        ('5', '5 Stars'),
        ('4', '4+ Stars'),
        ('3', '3+ Stars'),
        ('2', '2+ Stars'),
        ('1', '1+ Stars'),
    ]
    
    SENTIMENT_CHOICES = [
        ('', 'All Sentiments'),
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
    ]
    
    SORT_CHOICES = [
        ('-created_at', 'Newest First'),
        ('created_at', 'Oldest First'),
        ('-overall_rating', 'Highest Rated'),
        ('overall_rating', 'Lowest Rated'),
        ('-helpfulness_votes', 'Most Helpful'),
    ]
    
    search_query = forms.CharField(
        required=False,
        label='Search Reviews',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by keywords...',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    rating_filter = forms.ChoiceField(
        choices=RATING_CHOICES,
        required=False,
        label='Rating',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    sentiment_filter = forms.ChoiceField(
        choices=SENTIMENT_CHOICES,
        required=False,
        label='Sentiment',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='-created_at',
        label='Sort By',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    photographer = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )


class ReviewAnalyticsFilterForm(forms.Form):
    """Form for filtering analytics data"""
    
    PERIOD_CHOICES = [
        ('7', 'Last 7 days'),
        ('30', 'Last 30 days'),
        ('90', 'Last 3 months'),
        ('365', 'Last year'),
        ('all', 'All time'),
    ]
    
    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        initial='30',
        label='Time Period',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'this.form.submit();'
        })
    )
    
    include_unverified = forms.BooleanField(
        required=False,
        initial=False,
        label='Include unverified reviews',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'onchange': 'this.form.submit();'
        })
    )


class AnonymousReviewForm(forms.ModelForm):
    """Simplified review form for anonymous users"""
    
    # Anonymous user information - NAME IS REQUIRED
    anonymous_name = forms.CharField(
        max_length=100,
        required=True,
        label='Your Name *',
        help_text='Please enter your name (required)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name',
            'style': 'margin-bottom: 1rem;',
            'required': 'required'
        })
    )
    
    anonymous_email = forms.EmailField(
        required=False,
        label='Your Email (Optional)',
        help_text='We will not publish your email. Used only for verification.',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    photographer_id = forms.IntegerField(
        widget=forms.HiddenInput()
    )
    
    # Star ratings
    overall_rating = forms.IntegerField(
        min_value=1, max_value=5,
        label='Overall Rating',
        widget=forms.NumberInput(attrs={
            'class': 'form-control star-rating',
            'data-rating': 'overall',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    quality_rating = forms.IntegerField(
        min_value=1, max_value=5,
        label='Photo Quality',
        widget=forms.NumberInput(attrs={
            'class': 'form-control star-rating',
            'data-rating': 'quality',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    professionalism_rating = forms.IntegerField(
        min_value=1, max_value=5,
        label='Professionalism',
        widget=forms.NumberInput(attrs={
            'class': 'form-control star-rating',
            'data-rating': 'professionalism',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    communication_rating = forms.IntegerField(
        min_value=1, max_value=5,
        label='Communication',
        widget=forms.NumberInput(attrs={
            'class': 'form-control star-rating',
            'data-rating': 'communication',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    value_rating = forms.IntegerField(
        min_value=1, max_value=5,
        label='Value for Money',
        widget=forms.NumberInput(attrs={
            'class': 'form-control star-rating',
            'data-rating': 'value',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    comment = forms.CharField(
        validators=[MinLengthValidator(20, 'Please provide at least 20 characters in your review.')],
        label='Your Review',
        help_text='Share your experience (minimum 20 characters)',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Tell others about your experience with this photographer...',
            'style': 'margin-bottom: 1rem;'
        })
    )
    
    class Meta:
        model = Review
        fields = [
            'overall_rating', 'quality_rating', 'professionalism_rating',
            'communication_rating', 'value_rating', 'comment'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add helpful text
        self.fields['overall_rating'].help_text = 'Rate your overall experience (1-5 stars)'
        self.fields['quality_rating'].help_text = 'Rate the quality of photos received'
        self.fields['professionalism_rating'].help_text = 'Rate photographer\'s professionalism'
        self.fields['communication_rating'].help_text = 'Rate communication throughout the process'
        self.fields['value_rating'].help_text = 'Rate value for money paid'
        
        # Make name field extra clear that it's required
        self.fields['anonymous_name'].widget.attrs.update({
            'data-validation': 'required',
            'aria-required': 'true'
        })
    
    def clean_anonymous_name(self):
        """Custom validation for anonymous name field"""
        name = self.cleaned_data.get('anonymous_name', '').strip()
        
        if not name:
            raise forms.ValidationError('Name is required. Please enter your name.')
        
        if len(name) < 2:
            raise forms.ValidationError('Name must be at least 2 characters long.')
        
        if name.lower() in ['anonymous', 'anon', 'guest', 'user', 'test']:
            raise forms.ValidationError('Please enter your real name instead of a generic placeholder.')
        
        return name
