from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from .models import Address, Cart, CartItem, Order, OrderItem


SHIPPING_FLAT_RATE = Decimal('10.00')


class CartService:
    """Application service for cart write operations."""

    SHIPPING_FLAT_RATE = SHIPPING_FLAT_RATE

    @staticmethod
    @transaction.atomic
    def add_product_for_user(*, user, product, quantity=1):
        """Add product units to the customer cart respecting stock limits."""
        if quantity < 1:
            raise ValidationError(
                {'quantity': _('Quantity must be greater than zero.')},
            )

        cart, _created = Cart.objects.select_for_update().get_or_create(
            user=user,
        )

        cart_item = (
            CartItem.objects.select_for_update()
            .filter(cart=cart, product=product)
            .first()
        )

        existing_quantity = cart_item.quantity if cart_item else 0
        requested_quantity = existing_quantity + quantity

        if requested_quantity > product.stock:
            raise ValidationError(
                {
                    'quantity': _(
                        'You cannot add more units than the available stock.',
                    )
                },
            )

        if cart_item:
            cart_item.quantity = requested_quantity
            cart_item.save(update_fields=['quantity'])
            return cart_item, False

        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=quantity,
        )
        return cart_item, True

    @staticmethod
    @transaction.atomic
    def update_item_quantity_for_user(*, user, cart_item_id, quantity):
        """Update quantity for one cart item that belongs to the user."""
        if quantity < 1:
            raise ValidationError(
                {'quantity': _('Quantity must be greater than zero.')},
            )

        cart_item = get_object_or_404(
            CartItem.objects.select_related('product', 'cart').select_for_update(),
            pk=cart_item_id,
            cart__user=user,
        )

        if quantity > cart_item.product.stock:
            raise ValidationError(
                {
                    'quantity': _(
                        'You cannot set more units than the available stock.',
                    )
                },
            )

        cart_item.quantity = quantity
        cart_item.save(update_fields=['quantity'])
        return cart_item

    @staticmethod
    @transaction.atomic
    def remove_item_for_user(*, user, cart_item_id):
        """Delete one cart item that belongs to the user."""
        cart_item = get_object_or_404(
            CartItem.objects.select_related('cart').select_for_update(),
            pk=cart_item_id,
            cart__user=user,
        )
        product_name = cart_item.product.name
        cart_item.delete()
        return product_name

    @staticmethod
    @transaction.atomic
    def checkout_for_user(*, user, address_data):
        """Create order and items from cart, then clear cart."""
        cart = (
            Cart.objects.select_for_update()
            .filter(user=user)
            .first()
        )

        if cart is None:
            raise ValidationError(_('Your cart is empty.'))

        cart_items = list(
            cart.items.select_related('product').select_for_update(),
        )
        if not cart_items:
            raise ValidationError(_('Your cart is empty.'))

        shipping_address = CartService._resolve_shipping_address(
            user=user,
            address_data=address_data,
        )

        for cart_item in cart_items:
            product = cart_item.product
            if not product.is_available or cart_item.quantity > product.stock:
                raise ValidationError(
                    _(
                        'Stock changed for %(product)s. '
                        'Please update your cart.',
                    ) % {'product': product.name},
                )

        subtotal = sum(
            (item.product.price * item.quantity for item in cart_items),
            Decimal('0.00'),
        )
        shipping_cost = SHIPPING_FLAT_RATE
        total_amount = subtotal + shipping_cost

        order = Order.objects.create(
            user=user,
            shipping_address=shipping_address,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total_amount=total_amount,
            status=Order.STATUS_PENDING,
        )

        order_items = []
        for cart_item in cart_items:
            product = cart_item.product
            product.stock -= cart_item.quantity
            if product.stock == 0:
                product.is_available = False
            product.save(update_fields=['stock', 'is_available'])

            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=cart_item.quantity,
                    unit_price=product.price,
                )
            )

        OrderItem.objects.bulk_create(order_items)
        cart.items.all().delete()

        return order

    @staticmethod
    def _resolve_shipping_address(*, user, address_data):
        option = address_data.get('address_option')
        if option == 'existing':
            return get_object_or_404(
                Address,
                pk=address_data['address_id'],
                user=user,
            )

        is_default = bool(address_data.get('is_default'))
        if is_default:
            Address.objects.filter(user=user, is_default=True).update(
                is_default=False,
            )

        return Address.objects.create(
            user=user,
            street=address_data['street'],
            city=address_data['city'],
            state=address_data['state'],
            zip_code=address_data['zip_code'],
            country=address_data['country'],
            is_default=is_default,
        )
