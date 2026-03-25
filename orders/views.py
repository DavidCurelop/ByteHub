from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _

from .models import Order, Payment
from .services import PDFInvoiceProvider


@login_required
def order_list(request):
    """Display all orders for the authenticated user."""
    orders = Order.objects.get_user_orders_with_details(request.user.pk)
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    """Display the detail of a single order owned by the authenticated user."""
    order = get_object_or_404(
        Order.objects.select_related('user', 'shipping_address', 'payment')
        .prefetch_related('items__product'),
        pk=order_id,
        user=request.user,
    )
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def generate_invoice(request, order_id):
    """
    Generate and return a PDF invoice for an order.

    Only the order owner may request this. The order must have an
    associated payment with status ``completed``.
    """
    order = get_object_or_404(
        Order.objects.select_related('user', 'shipping_address', 'payment')
        .prefetch_related('items__product'),
        pk=order_id,
        user=request.user,
    )

    # Only allow invoice download when payment is completed.
    if not order.is_paid:
        raise Http404

    provider = PDFInvoiceProvider()
    pdf_bytes = provider.generate(order)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="invoice_{order.pk}.pdf"'
    )
    return response
