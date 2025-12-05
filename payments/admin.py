from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from django.template.response import TemplateResponse
from django.contrib.admin import AdminSite
from .models import (
    Transaction, PaymentGateway, PlatformCommission, 
    PhotographerPayout, PlatformRevenue,
    SubscriptionPlan, UserSubscription, SubscriptionPayment
)


# Custom admin site with dashboard
class PaymentsAdminSite(AdminSite):
    site_header = 'Photography Platform - Payment Management'
    site_title = 'Payment Admin'
    index_title = 'Payment & Subscription Dashboard'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('payments-dashboard/', self.admin_view(self.payments_dashboard), name='payments_dashboard'),
        ]
        return custom_urls + urls
    
    def payments_dashboard(self, request):
        """Enhanced dashboard with subscription and payment metrics"""
        # Subscription metrics
        total_subscriptions = UserSubscription.objects.count()
        active_subscriptions = UserSubscription.objects.filter(status='active').count()
        trial_subscriptions = UserSubscription.objects.filter(status='trial').count()
        
        # Revenue metrics
        total_revenue = SubscriptionPayment.objects.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Plan distribution
        plan_distribution = UserSubscription.objects.values(
            'plan__name', 'plan__display_name'
        ).annotate(count=Count('id'))
        
        # Recent activity
        recent_subscriptions = UserSubscription.objects.select_related(
            'user', 'plan'
        ).order_by('-created_at')[:5]
        
        recent_payments = SubscriptionPayment.objects.select_related(
            'subscription__user', 'subscription__plan'
        ).order_by('-created_at')[:5]
        
        context = {
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'trial_subscriptions': trial_subscriptions,
            'total_revenue': total_revenue,
            'plan_distribution': plan_distribution,
            'recent_subscriptions': recent_subscriptions,
            'recent_payments': recent_payments,
            'conversion_rate': round((active_subscriptions / max(total_subscriptions, 1)) * 100, 1),
        }
        
        return TemplateResponse(request, 'admin/payments_dashboard.html', context)

# Use custom admin site
admin_site = PaymentsAdminSite(name='admin')


@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'supports_escrow', 'processing_fee_display', 'currency')
    list_filter = ('is_active', 'supports_escrow', 'currency')
    search_fields = ('name',)
    
    def processing_fee_display(self, obj):
        return f"{obj.processing_fee_percentage * 100:.2f}% + {obj.fixed_fee} {obj.currency}"
    processing_fee_display.short_description = 'Processing Fee'


@admin.register(PlatformCommission)
class PlatformCommissionAdmin(admin.ModelAdmin):
    list_display = ('commission_percentage', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('created_at',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ('commission_percentage',)
        return self.readonly_fields


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id_short', 'transaction_type', 'user_link', 'booking_link', 
        'amount_display', 'commission_amount', 'net_amount', 'status_badge', 
        'gateway', 'created_at'
    )
    list_filter = (
        'transaction_type', 'status', 'gateway', 'created_at',
        'booking__service_type'
    )
    search_fields = (
        'transaction_id', 'user__email', 'user__first_name', 'user__last_name',
        'booking__id', 'external_transaction_id'
    )
    readonly_fields = (
        'transaction_id', 'commission_amount', 'net_amount', 'processing_fee',
        'created_at', 'updated_at', 'completed_at', 'escrow_released_at',
        'payment_method_details_display'
    )
    fieldsets = (
        ('Basic Information', {
            'fields': ('transaction_id', 'booking', 'user', 'transaction_type', 'status')
        }),
        ('Financial Details', {
            'fields': ('amount', 'currency', 'commission_rate', 'commission_amount', 
                      'processing_fee', 'net_amount')
        }),
        ('Payment Processing', {
            'fields': ('gateway', 'payment_method', 'external_transaction_id')
        }),
        ('Payment Method Details', {
            'fields': ('payment_method_details_display',),
            'description': 'Detailed payment information based on payment method used'
        }),
        ('Escrow & Completion', {
            'fields': ('escrow_released_at', 'escrow_release_reason', 'completed_at')
        }),
        ('Metadata', {
            'fields': ('description', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def payment_method_details_display(self, obj):
        """Display payment method specific details"""
        details = []
        
        if obj.card_last_four:
            details.append(f"<strong>Card Last 4:</strong> {obj.card_last_four}")
        if obj.card_brand:
            details.append(f"<strong>Card Brand:</strong> {obj.card_brand}")
        if obj.cardholder_name:
            details.append(f"<strong>Cardholder:</strong> {obj.cardholder_name}")
        
        if obj.mobile_money_provider:
            details.append(f"<strong>Provider:</strong> {obj.mobile_money_provider.upper()}")
        if obj.mobile_money_phone:
            details.append(f"<strong>Phone:</strong> {obj.mobile_money_phone}")
        
        if obj.paypal_email:
            details.append(f"<strong>PayPal Email:</strong> {obj.paypal_email}")
        if obj.paypal_payer_id:
            details.append(f"<strong>Payer ID:</strong> {obj.paypal_payer_id}")
        
        if obj.bank_reference:
            details.append(f"<strong>Bank Reference:</strong> {obj.bank_reference}")
        if obj.bank_name:
            details.append(f"<strong>Bank:</strong> {obj.bank_name}")
        
        if not details:
            return format_html('<em>No additional payment details</em>')
        
        return format_html('<br>'.join(details))
    payment_method_details_display.short_description = 'Payment Details'
    
    def transaction_id_short(self, obj):
        return str(obj.transaction_id)[:8] + '...'
    transaction_id_short.short_description = 'Transaction ID'
    
    def user_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name() or obj.user.email)
    user_link.short_description = 'User'
    
    def booking_link(self, obj):
        url = reverse('admin:bookings_booking_change', args=[obj.booking.id])
        return format_html('<a href="{}">{}</a>', url, f'Booking #{obj.booking.id}')
    booking_link.short_description = 'Booking'
    
    def amount_display(self, obj):
        return f"{obj.amount:,.2f} {obj.currency}"
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'gray',
            'refunded': 'purple',
            'held_escrow': 'gold'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    actions = ['release_escrow_action']
    
    def release_escrow_action(self, request, queryset):
        from .services import payment_service
        
        released_count = 0
        for transaction in queryset.filter(status='held_escrow'):
            result = payment_service.release_escrow(
                transaction.transaction_id, 
                "Admin manual release"
            )
            if result['success']:
                released_count += 1
        
        self.message_user(request, f'Released {released_count} transactions from escrow.')
    release_escrow_action.short_description = 'Release selected transactions from escrow'


@admin.register(PhotographerPayout)
class PhotographerPayoutAdmin(admin.ModelAdmin):
    list_display = (
        'payout_id_short', 'photographer_link', 'amount_display', 
        'method', 'status_badge', 'created_at'
    )
    list_filter = ('status', 'method', 'created_at')
    search_fields = (
        'payout_id', 'photographer__email', 'photographer__first_name',
        'photographer__last_name', 'recipient_account'
    )
    readonly_fields = ('payout_id', 'created_at', 'processed_at')
    
    def payout_id_short(self, obj):
        return str(obj.payout_id)[:8] + '...'
    payout_id_short.short_description = 'Payout ID'
    
    def photographer_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.photographer.id])
        return format_html('<a href="{}">{}</a>', url, obj.photographer.get_full_name())
    photographer_link.short_description = 'Photographer'
    
    def amount_display(self, obj):
        return f"{obj.amount:,.2f} {obj.currency}"
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(PlatformRevenue)
class PlatformRevenueAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'total_commission_display', 'total_transactions', 
        'net_revenue_display', 'updated_at'
    )
    list_filter = ('date', 'created_at')
    readonly_fields = (
        'total_commission', 'total_processing_fees', 'total_transactions',
        'net_revenue', 'created_at', 'updated_at'
    )
    date_hierarchy = 'date'
    
    def total_commission_display(self, obj):
        return f"{obj.total_commission:,.2f} RWF"
    total_commission_display.short_description = 'Commission'
    
    def net_revenue_display(self, obj):
        return f"{obj.net_revenue:,.2f} RWF"
    net_revenue_display.short_description = 'Net Revenue'
    
    def changelist_view(self, request, extra_context=None):
        # Add summary statistics to changelist
        response = super().changelist_view(request, extra_context)
        
        try:
            qs = response.context_data['cl'].queryset
            summary = qs.aggregate(
                total_revenue=Sum('net_revenue'),
                total_commission=Sum('total_commission'),
                total_transactions=Sum('total_transactions')
            )
            
            response.context_data['summary'] = {
                'total_revenue': summary['total_revenue'] or 0,
                'total_commission': summary['total_commission'] or 0,
                'total_transactions': summary['total_transactions'] or 0,
            }
        except (AttributeError, KeyError):
            pass
        
        return response


# Subscription Plan Administration
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = [
        'display_name_colored', 'name', 'price_monthly_display', 'currency', 
        'commission_rate_display', 'max_photos_upload', 'max_storage_display', 
        'subscriber_count', 'is_active_badge', 'created_at'
    ]
    list_filter = ['is_active', 'currency', 'created_at']
    search_fields = ['name', 'display_name', 'features_description']
    readonly_fields = ['created_at', 'updated_at', 'subscriber_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_name', 'features_description', 'is_active')
        }),
        ('Pricing', {
            'fields': ('price_monthly', 'price_yearly', 'currency', 'commission_rate'),
            'classes': ('wide',)
        }),
        ('Limits & Features', {
            'fields': (
                'max_photos_upload', 'max_storage_gb', 'max_bookings_per_month',
                'max_portfolio_items', 'support_level', 'customization_level',
                'additional_services'
            ),
            'classes': ('wide',)
        }),
        ('Platform Features', {
            'fields': (
                'priority_support', 'analytics_access', 'api_access',
                'includes_premium_support', 'includes_consulting', 'includes_add_ons'
            ),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def display_name_colored(self, obj):
        colors = {
            'basic': '#17a2b8',
            'standard': '#28a745', 
            'premium': '#ffc107'
        }
        color = colors.get(obj.name.lower(), '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">💎 {}</span>',
            color, obj.display_name
        )
    display_name_colored.short_description = 'Plan'
    
    def price_monthly_display(self, obj):
        return format_html(
            '<strong style="color: #28a745;">{} {}</strong>',
            f"{obj.price_monthly:,.0f}", obj.currency
        )
    price_monthly_display.short_description = 'Monthly Price'
    
    def commission_rate_display(self, obj):
        return format_html(
            '<span style="color: #dc3545;">{}</span>',
            f"{obj.commission_rate:.1f}%"
        )
    commission_rate_display.short_description = 'Commission'
    
    def max_storage_display(self, obj):
        if obj.max_storage_gb == -1:
            return format_html('<span style="color: #17a2b8;">♾️ Unlimited</span>')
        return f"{obj.max_storage_gb} GB"
    max_storage_display.short_description = 'Storage'
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #28a745;">✅ Active</span>')
        return format_html('<span style="color: #dc3545;">❌ Inactive</span>')
    is_active_badge.short_description = 'Status'
    
    def subscriber_count(self, obj):
        count = obj.usersubscription_set.count()
        return format_html(
            '<span style="color: #007bff; font-weight: bold;">{} users</span>',
            count
        )
    subscriber_count.short_description = 'Subscribers'


# User Subscription Administration  
@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user_link', 'plan_display', 'status_badge', 'usage_progress',
        'billing_cycle', 'next_billing_date', 'created_at'
    ]
    list_filter = ['status', 'billing_cycle', 'plan__name', 'auto_renew', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    ordering = ['-created_at']
    
    fieldsets = (
        ('User & Plan', {
            'fields': ('user', 'plan', 'billing_cycle', 'status')
        }),
        ('Subscription Dates', {
            'fields': ('start_date', 'end_date', 'next_billing_date', 'trial_end_date')
        }),
        ('Usage Tracking', {
            'fields': ('photos_uploaded_this_month', 'storage_used_gb', 'bookings_this_month', 'portfolio_items_count')
        }),
        ('Settings', {
            'fields': ('auto_renew', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def user_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:users_user_change', args=[obj.user.pk]),
            obj.user.get_full_name() or obj.user.username
        )
    user_link.short_description = 'User'
    
    def plan_display(self, obj):
        colors = {'basic': '#17a2b8', 'standard': '#28a745', 'premium': '#ffc107'}
        color = colors.get(obj.plan.name.lower(), '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.plan.display_name
        )
    plan_display.short_description = 'Plan'
    
    def status_badge(self, obj):
        colors = {'active': '#28a745', 'trial': '#ffc107', 'expired': '#dc3545', 'cancelled': '#6c757d'}
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.85em;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def usage_progress(self, obj):
        if obj.plan.max_photos_upload == -1:
            return "Unlimited"
        percentage = min((obj.photos_uploaded_this_month / obj.plan.max_photos_upload) * 100, 100)
        color = '#28a745' if percentage < 80 else '#ffc107' if percentage < 100 else '#dc3545'
        return format_html(
            '<div style="background: #f0f0f0; border-radius: 10px; height: 20px; width: 100px; overflow: hidden;">'
            '<div style="background: {}; height: 100%; width: {}%;"></div></div>'
            '<small>{}/{}</small>',
            color, f"{percentage:.1f}", obj.photos_uploaded_this_month, obj.plan.max_photos_upload
        )
    usage_progress.short_description = 'Photo Usage'


# Subscription Payment Administration
@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'subscription_user', 'plan_name', 'amount_display', 'status_badge',
        'payment_method', 'payment_details_short', 'paid_at', 'created_at'
    ]
    list_filter = ['status', 'payment_method', 'payment_gateway', 'currency', 'created_at']
    search_fields = [
        'subscription__user__username', 'subscription__user__email',
        'transaction_id', 'gateway_transaction_id', 'invoice_number',
        'card_last_four', 'mobile_money_phone', 'paypal_email'
    ]
    ordering = ['-created_at']
    readonly_fields = ['transaction_id', 'payment_method_details_display', 'created_at', 'updated_at', 'paid_at']
    
    fieldsets = (
        ('Subscription Information', {
            'fields': ('subscription', 'amount', 'currency', 'billing_period_start', 'billing_period_end')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_gateway', 'transaction_id', 'gateway_transaction_id', 'status', 'paid_at')
        }),
        ('Payment Method Details', {
            'fields': ('payment_method_details_display',),
            'description': 'Detailed payment information based on payment method used'
        }),
        ('Invoice', {
            'fields': ('invoice_number', 'invoice_url')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def subscription_user(self, obj):
        return obj.subscription.user.username
    subscription_user.short_description = 'User'
    
    def plan_name(self, obj):
        return obj.subscription.plan.display_name
    plan_name.short_description = 'Plan'
    
    def amount_display(self, obj):
        return format_html(
            '<strong style="color: #28a745;">{} {}</strong>',
            f"{obj.amount:,.0f}", obj.subscription.plan.currency
        )
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        colors = {'completed': '#28a745', 'pending': '#ffc107', 'failed': '#dc3545'}
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.85em;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def payment_details_short(self, obj):
        """Display brief payment details"""
        if obj.card_last_four:
            return format_html('<span title="Card payment">💳 ****{}</span>', obj.card_last_four)
        elif obj.mobile_money_phone:
            return format_html('<span title="Mobile Money">📱 {}</span>', obj.mobile_money_phone[-10:])
        elif obj.paypal_email:
            return format_html('<span title="PayPal">🅿️ {}</span>', obj.paypal_email[:20])
        return '—'
    payment_details_short.short_description = 'Payment Info'
    
    def payment_method_details_display(self, obj):
        """Display payment method specific details"""
        details = []
        
        if obj.card_last_four:
            details.append(f"<strong>Card Last 4:</strong> {obj.card_last_four}")
        if obj.card_brand:
            details.append(f"<strong>Card Brand:</strong> {obj.card_brand}")
        if obj.cardholder_name:
            details.append(f"<strong>Cardholder:</strong> {obj.cardholder_name}")
        
        if obj.mobile_money_provider:
            details.append(f"<strong>Provider:</strong> {obj.mobile_money_provider.upper()}")
        if obj.mobile_money_phone:
            details.append(f"<strong>Phone:</strong> {obj.mobile_money_phone}")
        
        if obj.paypal_email:
            details.append(f"<strong>PayPal Email:</strong> {obj.paypal_email}")
        if obj.paypal_payer_id:
            details.append(f"<strong>Payer ID:</strong> {obj.paypal_payer_id}")
        
        if not details:
            return format_html('<em>No additional payment details</em>')
        
        return format_html('<br>'.join(details))
    payment_method_details_display.short_description = 'Payment Details'
    
    def days_remaining(self, obj):
        days = obj.days_until_expiry()
        if days == 0:
            return format_html('<span style="color: red;">Expired</span>')
        elif days <= 7:
            return format_html('<span style="color: orange;">{} days</span>', days)
        else:
            return format_html('<span style="color: green;">{} days</span>', days)
    days_remaining.short_description = 'Days Remaining'
    
    actions = ['reset_monthly_usage', 'extend_subscription']
    
    def reset_monthly_usage(self, request, queryset):
        for subscription in queryset:
            subscription.reset_monthly_usage()
        self.message_user(request, f"Reset monthly usage for {queryset.count()} subscriptions.")
    reset_monthly_usage.short_description = "Reset monthly usage counters"
    
    def extend_subscription(self, request, queryset):
        from datetime import timedelta
        for subscription in queryset:
            subscription.end_date += timedelta(days=30)
            subscription.save()
        self.message_user(request, f"Extended {queryset.count()} subscriptions by 30 days.")
    extend_subscription.short_description = "Extend subscription by 30 days"
