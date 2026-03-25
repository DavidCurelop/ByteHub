from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .models import Cart, Order, OrderItem, Product


DEFAULT_SHIPPING_COST = Decimal('10.00')


def create_order_from_cart(user, shipping_address, shipping_cost=DEFAULT_SHIPPING_COST):
    """Create an order from the user's latest cart and clear cart items."""
    cart = Cart.objects.filter(user=user).prefetch_related('items__product').first()
    if cart is None:
        raise ValidationError(_('Your cart is empty.'))

    cart_items = list(cart.items.select_related('product'))
    if not cart_items:
        raise ValidationError(_('Your cart is empty.'))

    with transaction.atomic():
        product_ids = [item.product_id for item in cart_items]
        products_by_id = {
            product.id: product
            for product in Product.objects.select_for_update().filter(id__in=product_ids)
        }

        for item in cart_items:
            product = products_by_id[item.product_id]
            if item.quantity > product.stock:
                raise ValidationError(
                    _('Product "%(product)s" does not have enough stock.')
                    % {'product': product.name}
                )

        subtotal = sum(
            item.quantity * products_by_id[item.product_id].price
            for item in cart_items
        )
        total_amount = subtotal + shipping_cost

        order = Order.objects.create(
            user=user,
            shipping_address=shipping_address,
            status=Order.STATUS_CONFIRMED,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total_amount=total_amount,
        )

        order_items = []
        for item in cart_items:
            product = products_by_id[item.product_id]
            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    unit_price=product.price,
                )
            )
            product.stock -= item.quantity
            product.save(update_fields=['stock'])

        OrderItem.objects.bulk_create(order_items)
        cart.items.all().delete()

    return order
