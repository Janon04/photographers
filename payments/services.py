"""
Professional Payment Service for PhotoRw Platform
Handles commission-based payments, escrow, and payouts
"""

from decimal import Decimal
from django.db import transaction as db_transaction
from django.utils import timezone
from django.conf import settings
import stripe
import uuid
from .models import (
    Transaction, PaymentGateway, PlatformCommission, 
    PhotographerPayout, PlatformRevenue
)
from bookings.models import Booking


class PaymentService:
    """Main payment processing service"""
    
    def __init__(self):
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
    
    @db_transaction.atomic
    def process_client_payment(self, booking_id, amount, payment_method='stripe', customer_email=None):
        """
        Process client payment with commission calculation and escrow
        
        Args:
            booking_id: ID of the booking
            amount: Payment amount in RWF
            payment_method: Payment gateway (stripe, paypal, mobile_money)
            customer_email: Client email for payment
        
        Returns:
            dict: Payment result with transaction details
        """
        try:
            booking = Booking.objects.get(id=booking_id)
            gateway = PaymentGateway.objects.filter(
                name__icontains=payment_method, 
                is_active=True
            ).first()
            
            if not gateway:
                return {'success': False, 'error': 'Payment gateway not available'}
            
            # Create initial transaction
            transaction = Transaction.objects.create(
                booking=booking,
                user=booking.client,
                transaction_type=Transaction.TransactionType.CLIENT_PAYMENT,
                amount=Decimal(str(amount)),
                gateway=gateway,
                status=Transaction.TransactionStatus.PENDING,
                payment_method=payment_method,
                description=f"Payment for {booking.service_type} photography session"
            )
            
            # Calculate commission and fees
            transaction.calculate_commission_and_fees()
            
            # Process payment based on gateway
            if payment_method.lower() == 'stripe':
                result = self._process_stripe_payment(transaction, customer_email)
            elif payment_method.lower() == 'mobile_money':
                result = self._process_mobile_money_payment(transaction)
            else:
                result = {'success': False, 'error': 'Unsupported payment method'}
            
            if result['success']:
                # Move to escrow if payment successful
                transaction.status = Transaction.TransactionStatus.HELD_ESCROW
                transaction.external_transaction_id = result.get('payment_id', '')
                transaction.save()
                
                # Update booking payment status
                booking.payment_status = 'paid'
                booking.save()
                
                return {
                    'success': True,
                    'transaction_id': str(transaction.transaction_id),
                    'amount': transaction.amount,
                    'commission': transaction.commission_amount,
                    'net_amount': transaction.net_amount,
                    'payment_id': result.get('payment_id'),
                    'escrow_message': 'Payment held in escrow until service completion'
                }
            else:
                transaction.status = Transaction.TransactionStatus.FAILED
                transaction.save()
                return result
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _process_stripe_payment(self, transaction, customer_email):
        """Process payment through Stripe"""
        try:
            # Convert RWF to cents for Stripe (if RWF is supported) or handle currency conversion
            amount_cents = int(transaction.amount * 100)
            
            # Create Stripe Payment Intent
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='rwf',  # Check if Stripe supports RWF
                customer_email=customer_email,
                description=transaction.description,
                metadata={
                    'transaction_id': str(transaction.transaction_id),
                    'booking_id': transaction.booking.id,
                    'platform': 'PhotoRw'
                }
            )
            
            return {
                'success': True,
                'payment_id': intent.id,
                'client_secret': intent.client_secret,
                'requires_action': intent.status == 'requires_action'
            }
            
        except stripe.error.StripeError as e:
            return {'success': False, 'error': f'Stripe error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Payment processing error: {str(e)}'}
    
    def _process_mobile_money_payment(self, transaction):
        """Process mobile money payment (MTN, Airtel)"""
        # Integrate with local mobile money APIs
        # This is a placeholder - implement actual mobile money integration
        return {
            'success': True,
            'payment_id': f'momo_{uuid.uuid4().hex[:8]}',
            'message': 'Mobile money payment initiated'
        }
    
    @db_transaction.atomic
    def release_escrow(self, transaction_id, release_reason="Service completed"):
        """
        Release funds from escrow to photographer
        
        Args:
            transaction_id: UUID of the transaction
            release_reason: Reason for release
        
        Returns:
            dict: Release result
        """
        try:
            transaction = Transaction.objects.get(transaction_id=transaction_id)
            
            if transaction.status != Transaction.TransactionStatus.HELD_ESCROW:
                return {'success': False, 'error': 'Transaction not in escrow'}
            
            # Release escrow
            transaction.release_escrow(release_reason)
            
            # Calculate daily revenue
            PlatformRevenue.calculate_daily_revenue()
            
            return {
                'success': True,
                'message': 'Escrow released successfully',
                'payout_amount': transaction.net_amount,
                'photographer': transaction.booking.photographer.get_full_name()
            }
            
        except Transaction.DoesNotExist:
            return {'success': False, 'error': 'Transaction not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def auto_release_escrow(self, days=7):
        """
        Automatically release escrow after specified days
        
        Args:
            days: Number of days to wait before auto-release
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        # Find transactions in escrow older than cutoff date
        escrow_transactions = Transaction.objects.filter(
            status=Transaction.TransactionStatus.HELD_ESCROW,
            created_at__lt=cutoff_date
        )
        
        released_count = 0
        for transaction in escrow_transactions:
            try:
                transaction.release_escrow("Auto-release after 7 days")
                released_count += 1
            except Exception as e:
                print(f"Failed to auto-release transaction {transaction.transaction_id}: {e}")
        
        return released_count
    
    def process_photographer_payout(self, payout_id):
        """
        Process payout to photographer's bank account or mobile money
        
        Args:
            payout_id: UUID of the payout
        
        Returns:
            dict: Payout result
        """
        try:
            payout = PhotographerPayout.objects.get(payout_id=payout_id)
            
            if payout.status != PhotographerPayout.PayoutStatus.PENDING:
                return {'success': False, 'error': 'Payout already processed'}
            
            # Update status to processing
            payout.status = PhotographerPayout.PayoutStatus.PROCESSING
            payout.save()
            
            # Process based on method
            if payout.method == PhotographerPayout.PayoutMethod.STRIPE:
                result = self._process_stripe_payout(payout)
            elif payout.method == PhotographerPayout.PayoutMethod.MOBILE_MONEY:
                result = self._process_mobile_money_payout(payout)
            else:
                result = self._process_bank_transfer_payout(payout)
            
            if result['success']:
                payout.status = PhotographerPayout.PayoutStatus.COMPLETED
                payout.processed_at = timezone.now()
                payout.external_payout_id = result.get('payout_id', '')
                payout.save()
            else:
                payout.status = PhotographerPayout.PayoutStatus.FAILED
                payout.save()
            
            return result
            
        except PhotographerPayout.DoesNotExist:
            return {'success': False, 'error': 'Payout not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _process_stripe_payout(self, payout):
        """Process payout through Stripe"""
        # Implement Stripe payout to photographer's connected account
        return {'success': True, 'payout_id': f'stripe_payout_{uuid.uuid4().hex[:8]}'}
    
    def _process_mobile_money_payout(self, payout):
        """Process payout through mobile money"""
        # Implement mobile money payout
        return {'success': True, 'payout_id': f'momo_payout_{uuid.uuid4().hex[:8]}'}
    
    def _process_bank_transfer_payout(self, payout):
        """Process payout through bank transfer"""
        # Implement bank transfer payout
        return {'success': True, 'payout_id': f'bank_payout_{uuid.uuid4().hex[:8]}'}
    
    def get_revenue_analytics(self, start_date=None, end_date=None):
        """
        Get platform revenue analytics
        
        Args:
            start_date: Start date for analytics
            end_date: End date for analytics
        
        Returns:
            dict: Revenue analytics
        """
        if not start_date:
            start_date = timezone.now().date() - timezone.timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
        
        revenue_data = PlatformRevenue.objects.filter(
            date__range=[start_date, end_date]
        )
        
        total_commission = sum(r.total_commission for r in revenue_data)
        total_transactions = sum(r.total_transactions for r in revenue_data)
        
        return {
            'total_commission': total_commission,
            'total_transactions': total_transactions,
            'average_commission': total_commission / max(total_transactions, 1),
            'daily_data': [
                {
                    'date': r.date,
                    'commission': r.total_commission,
                    'transactions': r.total_transactions
                }
                for r in revenue_data
            ]
        }


class CommissionService:
    """Service for managing platform commission rates"""
    
    @staticmethod
    def update_commission_rate(new_rate, admin_user):
        """
        Update platform commission rate
        
        Args:
            new_rate: New commission percentage (0-50)
            admin_user: Admin user making the change
        
        Returns:
            PlatformCommission: New commission record
        """
        # Deactivate current rate
        PlatformCommission.objects.filter(is_active=True).update(is_active=False)
        
        # Create new rate
        new_commission = PlatformCommission.objects.create(
            commission_percentage=Decimal(str(new_rate)),
            is_active=True
        )
        
        return new_commission
    
    @staticmethod
    def get_commission_history():
        """Get commission rate history"""
        return PlatformCommission.objects.all()


class SubscriptionService:
    """Handle subscription business logic"""
    
    @staticmethod
    def get_or_create_user_subscription(user):
        """Get user's subscription or create a trial basic plan"""
        from .models import SubscriptionPlan, UserSubscription
        try:
            return user.subscription
        except UserSubscription.DoesNotExist:
            # Create trial subscription with basic plan
            basic_plan = SubscriptionPlan.objects.get(name='basic')
            subscription = UserSubscription.objects.create(
                user=user,
                plan=basic_plan,
                status='trial',
                billing_cycle='monthly'
            )
            return subscription
    
    @staticmethod
    def upgrade_subscription(user, new_plan_name, billing_cycle='monthly'):
        """Upgrade user's subscription to a new plan"""
        from .models import SubscriptionPlan
        with db_transaction.atomic():
            subscription = SubscriptionService.get_or_create_user_subscription(user)
            new_plan = SubscriptionPlan.objects.get(name=new_plan_name, is_active=True)
            
            # Calculate prorated amount if upgrading mid-cycle
            prorated_amount = SubscriptionService._calculate_prorated_amount(
                subscription, new_plan, billing_cycle
            )
            
            # Update subscription
            subscription.plan = new_plan
            subscription.billing_cycle = billing_cycle
            subscription.status = 'active'
            
            # Reset trial if it was a trial
            if subscription.status == 'trial':
                subscription.trial_end_date = None
            
            # Extend subscription period
            from datetime import timedelta
            if billing_cycle == 'yearly':
                subscription.end_date = timezone.now() + timedelta(days=365)
            else:
                subscription.end_date = timezone.now() + timedelta(days=30)
                
            subscription.next_billing_date = subscription.end_date
            subscription.save()
            
            return subscription, prorated_amount
    
    @staticmethod
    def _calculate_prorated_amount(subscription, new_plan, billing_cycle):
        """Calculate prorated amount for mid-cycle upgrades"""
        if billing_cycle == 'yearly':
            new_amount = new_plan.get_yearly_price()
        else:
            new_amount = new_plan.price_monthly
            
        if subscription.status == 'trial':
            return new_amount
            
        # Calculate remaining days in current cycle
        remaining_days = (subscription.end_date - timezone.now()).days
        
        if billing_cycle == 'yearly':
            total_days = 365
        else:
            total_days = 30
            
        # Calculate prorated amount
        daily_rate = new_amount / total_days
        prorated_amount = daily_rate * remaining_days
        
        return prorated_amount
    
    @staticmethod
    def check_usage_limits(user, action_type, count=1):
        """Check if user can perform an action based on their plan limits"""
        subscription = SubscriptionService.get_or_create_user_subscription(user)
        
        if not subscription.is_active():
            return False, "Subscription is not active"
            
        if action_type == 'upload_photos':
            if subscription.can_upload_photos(count):
                return True, "OK"
            else:
                return False, f"Monthly photo upload limit reached ({subscription.plan.max_photos_upload})"
                
        elif action_type == 'create_booking':
            if subscription.can_create_booking():
                return True, "OK"
            else:
                return False, f"Monthly booking limit reached ({subscription.plan.max_bookings_per_month})"
                
        elif action_type == 'add_storage':
            if subscription.can_add_storage(count):
                return True, "OK"
            else:
                return False, f"Storage limit reached ({subscription.plan.max_storage_gb}GB)"
        
        return True, "OK"
    
    @staticmethod
    def update_usage(user, action_type, count=1):
        """Update usage counters"""
        subscription = SubscriptionService.get_or_create_user_subscription(user)
        
        if action_type == 'upload_photos':
            subscription.photos_uploaded_this_month += count
        elif action_type == 'create_booking':
            subscription.bookings_this_month += count
        elif action_type == 'add_storage':
            subscription.storage_used_gb += Decimal(str(count))
        elif action_type == 'add_portfolio_item':
            subscription.portfolio_items_count += count
            
        subscription.save()


# Initialize payment service
payment_service = PaymentService()
commission_service = CommissionService()
subscription_service = SubscriptionService()