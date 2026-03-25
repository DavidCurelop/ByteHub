from django.db import transaction
from django.utils import timezone

from orders.models import (
    PAYMENT_STATUS_FAILED,
    PAYMENT_STATUS_SUCCEEDED,
    STATUS_PAID,
    Payment,
)


class PaymentProcessingService:
    """Workflow service for processing order payments."""

    def __init__(self, payment_provider):
        self.payment_provider = payment_provider

    @transaction.atomic
    def process_order_payment(self, order, payment_method, payment_data):
        result = self.payment_provider.process_payment(
            amount=order.total_amount,
            method=payment_method,
            data=payment_data,
        )
        payment_status = (
            PAYMENT_STATUS_SUCCEEDED
            if result.success
            else PAYMENT_STATUS_FAILED
        )

        payment, _ = Payment.objects.update_or_create(
            order=order,
            defaults={
                'payment_method': payment_method,
                'amount': order.total_amount,
                'status': payment_status,
                'transaction_id': result.transaction_id,
                'paid_at': timezone.now() if result.success else None,
            },
        )

        if result.success:
            order.status = STATUS_PAID
            order.save(update_fields=['status'])

        return result, payment