from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render

from core.invoice.pdf_provider import PDFInvoiceProvider
from store.models import Order


@login_required
def order_list(request):
    print("USER:", request.user)
    print("USER ID:", request.user.pk)
    print("AUTH:", request.user.is_authenticated)

    orders = Order.objects.get_user_orders_with_details(
        user_id=request.user.pk,
    )

    print("ORDERS:", orders)

    return render(
        request,
        'orders/list.html',
        {'orders': orders},
    )


@login_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.get_user_orders_with_details(request.user.pk),
        pk=pk,
    )

    items = order.items.all()

    user_order_number = Order.objects.filter(
        user=request.user,
        created_at__gte=order.created_at,
    ).count()

    return render(
        request,
        'orders/detail.html',
        {'order': order, 'items': items, 'user_order_number': user_order_number},
    )


@login_required
def generate_invoice(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if order.user_id != request.user.pk:
        raise PermissionDenied

    if order.status != Order.STATUS_PAID:
        raise Http404

    pdf_bytes = PDFInvoiceProvider().generate(order)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="invoice_order_{order.pk}.pdf"'
    )
    return response