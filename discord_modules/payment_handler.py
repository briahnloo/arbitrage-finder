"""
Payment Handler for Arbitrage Finder Premium Service
Handles Stripe integration for subscription payments
"""

import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import asyncio

load_dotenv()
logger = logging.getLogger(__name__)

try:
    import stripe
except ImportError:
    logger.warning('stripe library not installed. Install with: pip install stripe')
    stripe = None


class StripePaymentHandler:
    """Handles Stripe payment processing"""

    def __init__(self):
        self.api_key = os.getenv('STRIPE_API_KEY')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        self.product_id = os.getenv('STRIPE_PRODUCT_ID')
        self.price_id = os.getenv('STRIPE_PRICE_ID')

        if stripe and self.api_key:
            stripe.api_key = self.api_key

    def create_customer(self, discord_id: int, email: str, name: str) -> Optional[str]:
        """
        Create a new Stripe customer

        Args:
            discord_id: Discord user ID
            email: Customer email
            name: Customer name

        Returns:
            Stripe customer ID or None
        """
        if not stripe or not self.api_key:
            logger.error('Stripe not configured')
            return None

        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    'discord_id': str(discord_id)
                }
            )
            logger.info(f'Created Stripe customer {customer.id} for Discord user {discord_id}')
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f'Error creating customer: {e}')
            return None

    def create_subscription(self, customer_id: str, discord_id: int, trial_days: int = 7) -> Optional[str]:
        """
        Create a subscription for a customer

        Args:
            customer_id: Stripe customer ID
            discord_id: Discord user ID
            trial_days: Trial period in days

        Returns:
            Subscription ID or None
        """
        if not stripe or not self.api_key:
            logger.error('Stripe not configured')
            return None

        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': self.price_id}],
                trial_period_days=trial_days,
                metadata={
                    'discord_id': str(discord_id)
                }
            )
            logger.info(f'Created subscription {subscription.id} for Discord user {discord_id}')
            return subscription.id
        except stripe.error.StripeError as e:
            logger.error(f'Error creating subscription: {e}')
            return None

    def cancel_subscription(self, subscription_id: str) -> bool:
        """
        Cancel a subscription

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            True if successful, False otherwise
        """
        if not stripe or not self.api_key:
            logger.error('Stripe not configured')
            return False

        try:
            stripe.Subscription.delete(subscription_id)
            logger.info(f'Cancelled subscription {subscription_id}')
            return True
        except stripe.error.StripeError as e:
            logger.error(f'Error cancelling subscription: {e}')
            return False

    def get_subscription_status(self, subscription_id: str) -> Optional[Dict]:
        """
        Get subscription status

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Dictionary with subscription details or None
        """
        if not stripe or not self.api_key:
            logger.error('Stripe not configured')
            return None

        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                'id': subscription.id,
                'status': subscription.status,
                'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
                'trial_end': datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None,
                'customer_id': subscription.customer
            }
        except stripe.error.StripeError as e:
            logger.error(f'Error retrieving subscription: {e}')
            return None

    def process_webhook(self, payload: bytes, sig_header: str) -> Tuple[bool, Optional[Dict]]:
        """
        Process Stripe webhook event

        Args:
            payload: Webhook payload
            sig_header: Stripe signature header

        Returns:
            Tuple of (success: bool, event_data: dict)
        """
        if not stripe:
            logger.error('Stripe not configured')
            return False, None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )

            if event['type'] == 'customer.subscription.created':
                return True, {
                    'type': 'subscription_created',
                    'subscription_id': event['data']['object']['id'],
                    'customer_id': event['data']['object']['customer'],
                    'status': event['data']['object']['status']
                }

            elif event['type'] == 'customer.subscription.updated':
                return True, {
                    'type': 'subscription_updated',
                    'subscription_id': event['data']['object']['id'],
                    'customer_id': event['data']['object']['customer'],
                    'status': event['data']['object']['status']
                }

            elif event['type'] == 'customer.subscription.deleted':
                return True, {
                    'type': 'subscription_cancelled',
                    'subscription_id': event['data']['object']['id'],
                    'customer_id': event['data']['object']['customer']
                }

            elif event['type'] == 'invoice.payment_succeeded':
                return True, {
                    'type': 'payment_succeeded',
                    'invoice_id': event['data']['object']['id'],
                    'customer_id': event['data']['object']['customer'],
                    'amount': event['data']['object']['amount_paid']
                }

            elif event['type'] == 'invoice.payment_failed':
                return True, {
                    'type': 'payment_failed',
                    'invoice_id': event['data']['object']['id'],
                    'customer_id': event['data']['object']['customer'],
                    'amount': event['data']['object']['amount_due']
                }

            else:
                logger.info(f'Received unhandled webhook event: {event["type"]}')
                return True, {'type': 'unhandled', 'event_type': event['type']}

        except ValueError as e:
            logger.error(f'Invalid webhook payload: {e}')
            return False, None
        except stripe.error.SignatureVerificationError as e:
            logger.error(f'Invalid webhook signature: {e}')
            return False, None

    def create_payment_link(self, customer_id: str, success_url: str, cancel_url: str) -> Optional[str]:
        """
        Create a payment link for a customer

        Args:
            customer_id: Stripe customer ID
            success_url: URL to redirect on successful payment
            cancel_url: URL to redirect on cancelled payment

        Returns:
            Payment link URL or None
        """
        if not stripe or not self.api_key:
            logger.error('Stripe not configured')
            return None

        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                success_url=success_url,
                cancel_url=cancel_url,
                mode='subscription',
                line_items=[{
                    'price': self.price_id,
                    'quantity': 1
                }]
            )
            logger.info(f'Created payment link for customer {customer_id}')
            return session.url
        except stripe.error.StripeError as e:
            logger.error(f'Error creating payment link: {e}')
            return None


class MockPaymentHandler:
    """Mock payment handler for testing (when Stripe not available)"""

    def __init__(self):
        self.customers = {}
        self.subscriptions = {}

    def create_customer(self, discord_id: int, email: str, name: str) -> str:
        """Create mock customer"""
        customer_id = f'mock_cus_{discord_id}'
        self.customers[customer_id] = {
            'id': customer_id,
            'discord_id': discord_id,
            'email': email,
            'name': name
        }
        logger.info(f'Created mock customer {customer_id}')
        return customer_id

    def create_subscription(self, customer_id: str, discord_id: int, trial_days: int = 7) -> str:
        """Create mock subscription"""
        subscription_id = f'mock_sub_{discord_id}'
        self.subscriptions[subscription_id] = {
            'id': subscription_id,
            'customer_id': customer_id,
            'status': 'trialing',
            'trial_end': datetime.now() + timedelta(days=trial_days),
            'current_period_end': datetime.now() + timedelta(days=trial_days + 30)
        }
        logger.info(f'Created mock subscription {subscription_id}')
        return subscription_id

    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel mock subscription"""
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id]['status'] = 'cancelled'
            logger.info(f'Cancelled mock subscription {subscription_id}')
            return True
        return False

    def get_subscription_status(self, subscription_id: str) -> Optional[Dict]:
        """Get mock subscription status"""
        if subscription_id in self.subscriptions:
            sub = self.subscriptions[subscription_id]
            return {
                'id': sub['id'],
                'status': sub['status'],
                'current_period_end': sub['current_period_end'],
                'trial_end': sub.get('trial_end'),
                'customer_id': sub['customer_id']
            }
        return None

    def process_webhook(self, payload: bytes, sig_header: str) -> Tuple[bool, Optional[Dict]]:
        """Mock webhook processing"""
        logger.info('Mock webhook processed')
        return True, {'type': 'mock_webhook'}

    def create_payment_link(self, customer_id: str, success_url: str, cancel_url: str) -> str:
        """Create mock payment link"""
        return f'https://checkout.stripe.com/pay/mock_{customer_id}'


def get_payment_handler() -> 'PaymentHandler':
    """Get appropriate payment handler"""
    if stripe:
        logger.info('Using Stripe payment handler')
        return StripePaymentHandler()
    else:
        logger.warning('Using mock payment handler (Stripe not configured)')
        return MockPaymentHandler()
