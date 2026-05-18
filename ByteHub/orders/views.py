from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

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

    return render(
        request,
        'orders/detail.html',
        {'order': order, 'items': items},
    )