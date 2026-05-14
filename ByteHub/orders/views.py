from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from store.models import Order


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
