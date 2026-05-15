from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .models import Address, Cart, CartItem, Order, OrderItem, Product, Review


def add_product_to_cart(user, product_slug):
    """Add one unit of the product (by slug) to the user's cart.

    Raises ObjectDoesNotExist if the product slug is missing or inactive.
    Raises ValidationError when out of stock or already at the stock limit.
    Returns the CartItem.
    """
    try:
        product = Product.objects.get_active_products().get(slug=product_slug)
    except Product.DoesNotExist as exc:
        raise ObjectDoesNotExist(_('Product not found.')) from exc

    if product.stock < 1:
        raise ValidationError(_('This product is currently out of stock.'))

    with transaction.atomic():
        cart, _created = Cart.objects.get_or_create(user=user)
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 1},
        )

        if item_created:
            try:
                cart_item.full_clean()
            except ValidationError:
                cart_item.delete()
                raise ValidationError(
                    _('You cannot add more units than available stock.')
                )
        else:
            if cart_item.quantity >= product.stock:
                raise ValidationError(
                    _('You cannot add more units than available stock.')
                )
            cart_item.quantity += 1
            cart_item.full_clean()
            cart_item.save(update_fields=['quantity'])

    return cart_item


def _get_user_cart_item(user, item_id):
    try:
        return CartItem.objects.select_related('cart', 'product').get(
            id=item_id,
            cart__user=user,
        )
    except CartItem.DoesNotExist as exc:
        raise ObjectDoesNotExist(_('Cart item not found.')) from exc


def update_cart_item_quantity(user, item_id, quantity):
    """Set a new quantity for the user's cart item. Raises ValidationError if invalid."""
    cart_item = _get_user_cart_item(user, item_id)

    if quantity < 1:
        raise ValidationError(_('Quantity must be at least 1.'))

    if quantity > cart_item.product.stock:
        raise ValidationError(
            _('You cannot add more units than available stock.')
        )

    cart_item.quantity = quantity
    cart_item.full_clean()
    cart_item.save(update_fields=['quantity'])
    return cart_item


def delete_cart_item(user, item_id):
    """Remove an item from the user's cart."""
    cart_item = _get_user_cart_item(user, item_id)
    cart_item.delete()


def compute_checkout_summary(user, shipping_cost_when_empty=0):
    """Return ``(cart, items, subtotal, shipping_cost, total_amount)`` for the user.

    Shipping is DEFAULT_SHIPPING_COST when the cart is non-empty, else
    ``shipping_cost_when_empty``.
    """
    from orders.services import DEFAULT_SHIPPING_COST

    cart = Cart.objects.get_user_carts_with_details(user.id).first()
    cart_items = list(cart.items.all()) if cart else []

    subtotal = cart.get_total() if cart else 0
    shipping_cost = DEFAULT_SHIPPING_COST if cart_items else shipping_cost_when_empty
    total_amount = subtotal + shipping_cost
    return cart, cart_items, subtotal, shipping_cost, total_amount


def resolve_shipping_address(user, selected_address_id, address_data):
    """Return an Address for checkout: an existing user-owned one or a newly created one.

    ``address_data`` is a dict with keys street, city, state, zip_code, country, set_default.
    Raises ObjectDoesNotExist if selected_address_id does not belong to the user.
    Raises ValidationError when creating a new address with missing fields.
    """
    if selected_address_id and selected_address_id != 'new':
        try:
            return Address.objects.get(id=selected_address_id, user=user)
        except Address.DoesNotExist as exc:
            raise ObjectDoesNotExist(_('Shipping address not found.')) from exc

    required = ('street', 'city', 'state', 'zip_code', 'country')
    values = {key: (address_data.get(key) or '').strip() for key in required}
    if not all(values.values()):
        raise ValidationError(
            _('Please complete all shipping address fields.')
        )

    set_default = address_data.get('set_default') == 'on'

    with transaction.atomic():
        address = Address.objects.create(
            user=user,
            is_default=set_default,
            **values,
        )
        if set_default:
            Address.objects.filter(user=user).exclude(
                id=address.id,
            ).update(is_default=False)

    return address


@transaction.atomic
def create_review(*, user, product_slug, rating, title, body):
    """Create a verified-purchase review for ``product_slug`` by ``user``.

    Raises ObjectDoesNotExist when the product slug is missing or inactive.
    Raises ValidationError when the user has not purchased the product in a
    confirmed order.
    The Review model's UniqueConstraint on (product, user) enforces that a
    user cannot review the same product twice.
    Returns the created Review.
    """
    try:
        product = Product.objects.get_active_products().get(slug=product_slug)
    except Product.DoesNotExist as exc:
        raise ObjectDoesNotExist(_('Product not found.')) from exc

    has_purchased = OrderItem.objects.filter(
        product=product,
        order__user=user,
        order__status=Order.STATUS_CONFIRMED,
    ).exists()
    if not has_purchased:
        raise ValidationError(
            _('You can only review products you have purchased.')
        )

    return Review.objects.create(
        product=product,
        user=user,
        rating=rating,
        title=title or '',
        body=body or '',
        is_verified_purchase=True,
    )
