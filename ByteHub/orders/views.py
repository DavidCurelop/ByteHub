from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .models import Order


@login_required
def order_list(request):
    """Display a paginated history of the authenticated user's orders."""
    orders = Order.objects.get_user_orders_with_details(
        user_id=request.user.pk,
    )
    return render(
        request,
        'orders/order_list.html',
        {'orders': orders},
    )


@login_required
def order_detail(request, pk):
    """Display the full detail of a single order owned by the user."""
    order = get_object_or_404(Order, pk=pk)
    if order.user_id != request.user.pk:
        raise Http404
    items = order.items.select_related('product')
    return render(
        request,
        'orders/order_detail.html',
        {'order': order, 'items': items},
    )
