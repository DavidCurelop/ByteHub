"""Service layer for order-related workflows.

Defines abstract provider interfaces (Dependency Inversion Principle) and
concrete implementations for payment processing and invoice generation.
"""

import abc
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


# ---------------------------------------------------------------------------
# Data transfer objects
# ---------------------------------------------------------------------------

@dataclass
class ChargeResult:
    """Result returned by a payment provider after a charge attempt."""

    success: bool
    transaction_id: str
    amount: Decimal
    error_message: Optional[str] = field(default=None)


# ---------------------------------------------------------------------------
# Payment provider interface & implementations
# ---------------------------------------------------------------------------

class IPaymentProvider(abc.ABC):
    """Abstract interface for payment processing providers."""

    @abc.abstractmethod
    def charge(
        self,
        amount: Decimal,
        payment_method_token: str,
    ) -> ChargeResult:
        """Charge *amount* using the supplied payment method token.

        Args:
            amount: The amount to charge (must be > 0).
            payment_method_token: Provider-specific token representing the
                customer's payment method (e.g. Stripe PaymentMethod ID).

        Returns:
            A :class:`ChargeResult` describing the outcome of the charge.
        """

    @abc.abstractmethod
    def refund(self, transaction_id: str) -> bool:
        """Refund a previously completed charge.

        Args:
            transaction_id: The provider's unique identifier for the charge.

        Returns:
            ``True`` if the refund was issued successfully, ``False``
            otherwise.
        """


class StripePaymentProvider(IPaymentProvider):
    """Concrete Stripe implementation of :class:`IPaymentProvider`.

    In production, inject your Stripe secret key via the constructor or
    Django settings.  The ``stripe`` SDK is kept as an optional runtime
    dependency so the rest of the application can be tested without it.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        from django.conf import settings as django_settings

        self._api_key = api_key or getattr(
            django_settings, 'STRIPE_SECRET_KEY', ''
        )

    def _get_stripe(self):
        """Return the ``stripe`` module, raising ImportError if absent."""
        try:
            import stripe  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "The 'stripe' package is required to use "
                "StripePaymentProvider.  Install it with: "
                "pip install stripe"
            ) from exc
        stripe.api_key = self._api_key
        return stripe

    def charge(
        self,
        amount: Decimal,
        payment_method_token: str,
    ) -> ChargeResult:
        """Create a Stripe PaymentIntent and confirm it immediately."""
        stripe = self._get_stripe()
        # Stripe expects amounts in the smallest currency unit (cents).
        amount_cents = int(amount * 100)
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='usd',
                payment_method=payment_method_token,
                confirm=True,
                automatic_payment_methods={'enabled': True,
                                           'allow_redirects': 'never'},
            )
            return ChargeResult(
                success=True,
                transaction_id=intent['id'],
                amount=amount,
            )
        except Exception as exc:  # pragma: no cover – Stripe SDK exceptions
            return ChargeResult(
                success=False,
                transaction_id='',
                amount=amount,
                error_message=str(exc),
            )

    def refund(self, transaction_id: str) -> bool:
        """Issue a full refund for the given PaymentIntent ID."""
        stripe = self._get_stripe()
        try:
            stripe.Refund.create(payment_intent=transaction_id)
            return True
        except Exception:  # pragma: no cover
            return False


# ---------------------------------------------------------------------------
# Invoice provider interface & implementations
# ---------------------------------------------------------------------------

class IInvoiceProvider(abc.ABC):
    """Abstract interface for invoice generation."""

    @abc.abstractmethod
    def generate_invoice(self, order) -> bytes:
        """Generate an invoice document for *order*.

        Args:
            order: An :class:`orders.models.Order` instance.

        Returns:
            Raw bytes representing the invoice document (e.g. PDF content).
        """


class PDFInvoiceProvider(IInvoiceProvider):
    """Concrete implementation that generates a plain PDF invoice.

    Uses the ``reportlab`` library when available.  A lightweight fallback
    that produces a text/byte representation is used in environments where
    ``reportlab`` is not installed, so unit tests can run without it.
    """

    def generate_invoice(self, order) -> bytes:
        """Return a PDF invoice for *order* as raw bytes."""
        try:
            return self._generate_with_reportlab(order)
        except ImportError:
            return self._generate_text_fallback(order)

    def _generate_with_reportlab(self, order) -> bytes:
        """Generate a PDF using reportlab."""
        from io import BytesIO

        from reportlab.lib.pagesizes import A4  # noqa: PLC0415
        from reportlab.pdfgen import canvas  # noqa: PLC0415

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        pdf.setTitle(f'Invoice – Order #{order.pk}')
        y = height - 50

        def write_line(text, font='Helvetica', size=12, indent=50):
            nonlocal y
            pdf.setFont(font, size)
            pdf.drawString(indent, y, text)
            y -= size + 6

        write_line(f'ByteHub – Invoice', font='Helvetica-Bold', size=16)
        write_line(f'Order #{order.pk}', size=12)
        write_line(f'Customer: {order.user.get_full_name() or order.user}')
        write_line(
            f'Shipping: {order.shipping_address}'
        )
        write_line(f'Status: {order.get_status_display()}')
        write_line(f'Date: {order.created_at.strftime("%Y-%m-%d")}')
        y -= 10

        write_line('Items:', font='Helvetica-Bold')
        for item in order.items.select_related('product'):
            write_line(
                f'  {item.quantity} × {item.product.name}'
                f'  @ {item.unit_price}'
                f'  = {item.get_subtotal()}'
            )

        y -= 10
        write_line(f'Subtotal:      {order.subtotal}')
        write_line(f'Shipping cost: {order.shipping_cost}')
        write_line(
            f'Total:         {order.total_amount}',
            font='Helvetica-Bold',
        )

        pdf.save()
        return buffer.getvalue()

    @staticmethod
    def _generate_text_fallback(order) -> bytes:
        """Generate a minimal text-based invoice when reportlab is absent."""
        lines = [
            f'ByteHub Invoice',
            f'Order #{order.pk}',
            f'Customer: {order.user.get_full_name() or order.user}',
            f'Shipping: {order.shipping_address}',
            f'Status: {order.get_status_display()}',
            f'Date: {order.created_at.strftime("%Y-%m-%d")}',
            '',
            'Items:',
        ]
        for item in order.items.select_related('product'):
            lines.append(
                f'  {item.quantity} x {item.product.name}'
                f' @ {item.unit_price} = {item.get_subtotal()}'
            )
        lines += [
            '',
            f'Subtotal:      {order.subtotal}',
            f'Shipping cost: {order.shipping_cost}',
            f'Total:         {order.total_amount}',
        ]
        return '\n'.join(lines).encode('utf-8')
