from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from .models import PAYMENT_METHOD_STRIPE, STATUS_PAID, Order
from .services.payment_providers import StripePaymentProvider
from .services.payment_service import PaymentProcessingService


@login_required
def order_list(request):
    """Display the authenticated user's order history."""
    orders = Order.objects.get_user_orders_with_details(
        user_id=request.user.pk,
    )
    return render(
        request,
        'orders/list.html',
        {'orders': orders},
    )


@login_required
def order_detail(request, pk):
    """Display the full detail of a single order owned by the user."""
    order = get_object_or_404(
        Order.objects.get_user_orders_with_details(request.user.pk),
        pk=pk,
    )
    items = order.items.all()
    return render(
        request,
        'orders/detail.html',
        {'order': order, 'items': items},
    )


@login_required
def process_payment(request, order_id):
    """Process Stripe payment for an authenticated user's order."""
    order = get_object_or_404(
        Order.objects.select_related('payment').filter(user=request.user),
        pk=order_id,
    )

    if order.status == STATUS_PAID:
        messages.info(request, _('This order is already paid.'))
        return redirect('orders:order-detail', pk=order.pk)

    if request.method == 'POST':
        payment_provider = StripePaymentProvider()
        payment_service = PaymentProcessingService(
            payment_provider=payment_provider,
        )

        payment_result, _payment = payment_service.process_order_payment(
            order=order,
            payment_method=PAYMENT_METHOD_STRIPE,
            payment_data={
                'stripe_token': request.POST.get('stripe_token', '').strip(),
                'currency': 'usd',
                'description': _(
                    'ByteHub order payment #%(order_id)s'
                )
                % {'order_id': order.pk},
            },
        )

        if payment_result.success:
            messages.success(
                request,
                _(
                    'Payment completed successfully. '
                    'Transaction number: %(transaction_id)s'
                )
                % {'transaction_id': payment_result.transaction_id},
            )
            return redirect('orders:order-detail', pk=order.pk)

        messages.error(
            request,
            payment_result.error_message
            or _('Payment failed. Please verify your data and try again.'),
        )

    return render(
        request,
        'payment/form.html',
        {
            'order': order,
            'payment_method': PAYMENT_METHOD_STRIPE,
        },
    )
