import logging
import stripe
from django.conf import settings

logger = logging.getLogger(__name__)


class StripeService:

    def __init__(self):
        stripe.api_key = settings.STRIPE['SECRET_KEY']

    def create_payment_intent(self, amount_htg: float, transaction_number: str, metadata: dict = None):
        """
        Creates a Stripe PaymentIntent in HTG.
        Returns {'success': bool, 'client_secret': str, 'payment_intent_id': str, 'error': str}
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(round(float(amount_htg) * 100)),
                currency='htg',
                metadata={
                    'transaction_number': transaction_number,
                    **(metadata or {}),
                },
                automatic_payment_methods={'enabled': True},
            )
            return {
                'success': True,
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
            }
        except stripe.StripeError as e:
            logger.error(f'[Stripe] create_payment_intent error: {e}')
            return {'success': False, 'error': str(e)}

    def retrieve_payment_intent(self, payment_intent_id: str):
        """
        Returns {'success': bool, 'status': str, 'transaction_number': str, 'error': str}
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                'success': True,
                'status': intent.status,
                'transaction_number': intent.metadata.get('transaction_number', ''),
            }
        except stripe.StripeError as e:
            logger.error(f'[Stripe] retrieve_payment_intent error: {e}')
            return {'success': False, 'error': str(e)}

    def construct_webhook_event(self, payload: bytes, sig_header: str):
        """
        Validates Stripe webhook signature and returns the event.
        Returns {'success': bool, 'event': event, 'error': str}
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE['WEBHOOK_SECRET']
            )
            return {'success': True, 'event': event}
        except (stripe.SignatureVerificationError, ValueError) as e:
            logger.warning(f'[Stripe] webhook validation failed: {e}')
            return {'success': False, 'error': str(e)}
