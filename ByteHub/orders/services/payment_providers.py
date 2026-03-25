from abc import ABC, abstractmethod
from dataclasses import dataclass

from django.conf import settings
from django.utils.translation import gettext_lazy as _


@dataclass
class PaymentResult:
    success: bool
    transaction_id: str = ''
    error_message: str = ''


class IPaymentProvider(ABC):
    """Contract for external payment providers."""

    @abstractmethod
    def process_payment(self, amount, method, data):
        """Process a payment and return a provider-agnostic result."""


class StripePaymentProvider(IPaymentProvider):
    """Stripe-backed payment provider implementation."""

    def __init__(self, api_key=None):
        self.api_key = api_key or getattr(settings, 'STRIPE_SECRET_KEY', '')

    def process_payment(self, amount, method, data):
        if method != 'stripe':
            return PaymentResult(
                success=False,
                error_message=str(_('Unsupported payment method.')),
            )

        stripe_token = data.get('stripe_token', '').strip()
        if not stripe_token:
            return PaymentResult(
                success=False,
                error_message=str(_('Stripe token is required.')),
            )

        if not self.api_key:
            return PaymentResult(
                success=False,
                error_message=str(_('Stripe is not configured.')),
            )

        try:
            import stripe
            from stripe.error import StripeError
        except ImportError:
            return PaymentResult(
                success=False,
                error_message=str(_('Stripe SDK is not installed.')),
            )

        stripe.api_key = self.api_key

        try:
            charge = stripe.Charge.create(
                amount=int(amount * 100),
                currency=data.get('currency', 'usd'),
                source=stripe_token,
                description=data.get('description', ''),
            )
        except StripeError as error:
            return PaymentResult(
                success=False,
                error_message=str(error),
            )

        if charge.get('paid') and charge.get('status') == 'succeeded':
            return PaymentResult(
                success=True,
                transaction_id=charge.get('id', ''),
            )

        return PaymentResult(
            success=False,
            error_message=str(_('Payment could not be completed.')),
        )