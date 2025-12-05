# Payment System Documentation

## Overview
The PhotoRw platform has a comprehensive payment system that supports multiple payment methods for both client bookings and photographer subscriptions.

## Features

### 1. Client Payment System
- **Booking Payments**: Clients can pay for photography services
- **Multiple Payment Methods**:
  - Credit/Debit Cards (via Stripe)
  - Mobile Money (MTN, Airtel)
  - PayPal
  - Bank Transfer
- **Secure Checkout**: User-friendly checkout page with payment method selection
- **Payment Status Tracking**: Real-time payment status updates
- **Success/Failure Pages**: Clear feedback after payment attempts

### 2. Subscription Payment System
- **Photographer Subscriptions**: Three-tier subscription plans (Basic, Standard, Premium)
- **Flexible Billing**: Monthly or Yearly billing cycles
- **Feature-based Plans**: Different limits for photos, storage, and bookings
- **Subscription Management**: View and manage active subscriptions
- **Payment History**: Track all subscription payments

### 3. Platform Revenue Management
- **Commission Tracking**: Automatic calculation of platform commissions
- **Revenue Analytics**: Detailed revenue reports and trends
- **Multiple Revenue Streams**:
  - Booking commissions (10% default)
  - Subscription payments
- **Admin Dashboard**: Comprehensive revenue management interface

## URLs

### Client Payment URLs
- **Checkout**: `/payments/checkout/<booking_id>/` - Payment checkout page for a booking
- **Process Payment**: `/payments/checkout/<booking_id>/process/` - POST endpoint to process payment
- **Success**: `/payments/success/<transaction_id>/` - Payment success page
- **Failed**: `/payments/failed/<booking_id>/` - Payment failure page

### Subscription URLs
- **Pricing Page**: `/payments/pricing/` - View all subscription plans
- **Subscription Dashboard**: `/payments/subscription/` - Manage your subscription
- **Subscription Checkout**: `/payments/subscription/checkout/<plan_id>/` - Subscribe to a plan
- **Process Subscription**: `/payments/subscription/payment/process/` - POST endpoint for subscription payment

### Admin URLs
- **Platform Revenue**: `/admin-dashboard/revenue/` - Platform revenue management
- **Subscription Payments**: `/admin-dashboard/subscriptions/payments/` - View all subscription payments
- **Platform Revenue (Django Admin)**: `/admin/payments/platformrevenue/` - Django admin interface

## Payment Flow

### Client Booking Payment
1. Client creates a booking
2. Client is directed to payment checkout page
3. Client selects payment method
4. Payment is processed through the selected gateway
5. Payment is held in escrow until service completion
6. Upon service completion, payment is released to photographer
7. Platform commission is automatically calculated and recorded

### Subscription Payment
1. Photographer views subscription plans
2. Photographer selects a plan and billing cycle
3. Photographer is directed to subscription checkout
4. Payment is processed
5. Subscription is activated immediately
6. Auto-renewal is set for the next billing period

## Configuration

### Environment Variables
Add these to your `.env` file:

```env
# Stripe Configuration
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# PayPal Configuration
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret
PAYPAL_MODE=sandbox

# MTN Mobile Money
MTN_MOMO_API_KEY=your_api_key
MTN_MOMO_USER_ID=your_user_id
MTN_MOMO_SUBSCRIPTION_KEY=your_subscription_key
MTN_MOMO_ENVIRONMENT=sandbox

# Airtel Money
AIRTEL_MONEY_CLIENT_ID=your_client_id
AIRTEL_MONEY_CLIENT_SECRET=your_client_secret
AIRTEL_MONEY_ENVIRONMENT=sandbox
```

### Platform Settings
In `config/settings.py`:
- `PLATFORM_COMMISSION_RATE`: Default 10%
- `PLATFORM_PROCESSING_FEE_RATE`: Default 2.5%
- `PAYMENT_ESCROW_RELEASE_DAYS`: Default 7 days
- `PAYMENT_MIN_AMOUNT`: 1,000 RWF
- `PAYMENT_MAX_AMOUNT`: 10,000,000 RWF

## Database Models

### Transaction
Tracks all payment transactions with:
- Transaction type (client payment, commission, payout)
- Amount and currency
- Status (pending, completed, failed, held_escrow)
- Commission calculation
- Payment gateway details

### SubscriptionPayment
Records subscription payments with:
- Subscription reference
- Amount and billing period
- Payment method and gateway
- Status tracking

### PlatformRevenue
Daily revenue aggregation:
- Total commissions
- Processing fees
- Transaction counts
- Net revenue

## Payment Methods

### 1. Stripe (Credit/Debit Cards)
- Supports major credit/debit cards
- PCI-compliant payment processing
- Automatic 3D Secure authentication
- Webhook support for payment events

### 2. Mobile Money
**MTN Mobile Money**
- Rwanda's leading mobile payment platform
- Instant payment confirmation
- USSD and API integration

**Airtel Money**
- Alternative mobile payment option
- Wide coverage in Rwanda
- Simple integration

### 3. PayPal
- International payment support
- Buyer protection
- Express checkout

### 4. Bank Transfer
- Direct bank account transfers
- Manual verification required
- Longer processing time

## Commission System

### How It Works
1. Client pays total booking amount
2. Platform calculates commission (default 10%)
3. Payment held in escrow until service completion
4. Upon completion:
   - Photographer receives: Amount - Commission - Processing Fee
   - Platform receives: Commission
   - Gateway receives: Processing Fee

### Example Calculation
```
Booking Amount: 100,000 RWF
Platform Commission (10%): 10,000 RWF
Processing Fee (2.5%): 2,500 RWF
Photographer Receives: 87,500 RWF
Platform Revenue: 10,000 RWF
```

## Security Features

1. **PCI Compliance**: All card payments through PCI-compliant gateways
2. **Encryption**: SSL/TLS encryption for all payment data
3. **Escrow System**: Payments held until service completion
4. **Fraud Detection**: Automatic fraud detection through payment gateways
5. **Audit Trail**: Complete transaction history and logging

## Testing

### Test Mode
Use sandbox/test credentials for all payment gateways during development:
- Stripe test cards: `4242 4242 4242 4242`
- PayPal sandbox accounts
- Mobile Money sandbox environments

### Test Scenarios
1. Successful payment
2. Failed payment (insufficient funds)
3. Payment timeout
4. Refund processing
5. Subscription renewal

## Admin Functions

### Revenue Management
- View daily/monthly/yearly revenue
- Track commission earnings
- Monitor subscription income
- Export revenue reports

### Payment Monitoring
- Real-time transaction monitoring
- Payment status updates
- Failed payment alerts
- Refund processing

### Analytics
- Revenue trends over time
- Payment method distribution
- Top earning photographers
- Subscription metrics

## Troubleshooting

### Common Issues

**Payment Fails**
- Verify payment gateway credentials
- Check webhook configuration
- Review payment gateway logs
- Ensure adequate balance/credit

**Subscription Not Activating**
- Check subscription payment status
- Verify billing cycle configuration
- Review subscription service logic

**Commission Not Calculated**
- Verify transaction type
- Check commission rate settings
- Review transaction status

## Support

For payment-related issues:
- Email: support@photorw.com
- Phone: +250 788 123 456

For technical support:
- Developer email: janon3030@gmail.com
- Review payment logs in Django admin
- Check transaction records in database

## Future Enhancements

1. **Cryptocurrency Payments**: Bitcoin, Ethereum support
2. **Buy Now Pay Later**: Installment payment options
3. **Multi-currency**: Support for USD, EUR, GBP
4. **Automated Payouts**: Scheduled photographer payouts
5. **Advanced Analytics**: ML-based fraud detection
6. **Mobile App Integration**: In-app payment processing

## Compliance

- **PCI DSS**: Level 1 Service Provider compliance via Stripe
- **GDPR**: Payment data handling compliant with EU regulations
- **Local Regulations**: Compliant with Rwanda payment regulations
- **Data Retention**: 7-year transaction record retention

## API Documentation

For API integration, see:
- `payments/services.py` - PaymentService class
- `payments/views.py` - Payment view functions
- API endpoints documentation (coming soon)

---

Last Updated: December 2025
Version: 2.0
