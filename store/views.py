from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from .models import Address, Cart, CartItem, Product
from .services import DEFAULT_SHIPPING_COST, create_order_from_cart


def product_list(request):
    raw_search_query = request.GET.get('q', '')
    products = Product.objects.search_active_products_by_name(
        raw_search_query,
    )
    search_query = raw_search_query.strip()
    return render(
        request, 'store/product_list.html',
        {
            'products': products,
            'search_query': search_query,
            'is_searching': bool(search_query),
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.get_public_detail(),
        slug=slug,
    )
    context = {
        'product': product,
        'verified_reviews': product.verified_reviews,
        'average_rating': product.avg_rating(),
    }
    return render(request, 'store/product_detail.html', context)


@login_required
@require_POST
def add_to_cart(request, slug):
    product = get_object_or_404(
        Product.objects.get_active_products(),
        slug=slug,
    )
    if product.stock < 1:
        messages.error(
            request,
            _('This product is currently out of stock.'),
        )
        return redirect('store:product-detail', slug=product.slug)

    cart, _created = Cart.objects.get_or_create(user=request.user)
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
            messages.error(
                request,
                _(
                    'You cannot add more units than available stock.',
                ),
            )
            return redirect('store:product-detail', slug=product.slug)
    else:
        if cart_item.quantity >= product.stock:
            messages.error(
                request,
                _(
                    'You cannot add more units than available stock.',
                ),
            )
            return redirect('store:product-detail', slug=product.slug)
        cart_item.quantity += 1
        cart_item.full_clean()
        cart_item.save(update_fields=['quantity'])

    messages.success(request, _('Product added to your cart.'))
    return redirect('store:product-detail', slug=product.slug)


@login_required
def cart_detail(request):
    cart = Cart.objects.get_user_carts_with_details(request.user.id).first()
    cart_items = cart.items.all() if cart else []
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'store/cart_detail.html', context)


@login_required
@require_POST
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(
        CartItem.objects.select_related('cart', 'product'),
        id=item_id,
        cart__user=request.user,
    )
    try:
        quantity = int(request.POST.get('quantity', '1'))
    except ValueError:
        quantity = 1

    if quantity < 1:
        messages.error(request, _('Quantity must be at least 1.'))
        return redirect('store:cart-detail')

    if quantity > cart_item.product.stock:
        messages.error(
            request,
            _('You cannot add more units than available stock.'),
        )
        return redirect('store:cart-detail')

    cart_item.quantity = quantity
    cart_item.full_clean()
    cart_item.save(update_fields=['quantity'])
    messages.success(request, _('Cart item quantity updated.'))
    return redirect('store:cart-detail')


@login_required
@require_POST
def delete_cart_item(request, item_id):
    cart_item = get_object_or_404(
        CartItem.objects.select_related('cart'),
        id=item_id,
        cart__user=request.user,
    )
    cart_item.delete()
    messages.success(request, _('Item removed from your cart.'))
    return redirect('store:cart-detail')


@login_required
def checkout(request):
    cart = Cart.objects.get_user_carts_with_details(request.user.id).first()
    cart_items = list(cart.items.all()) if cart else []
    addresses = Address.objects.filter(user=request.user)

    subtotal = cart.get_total() if cart else 0
    shipping_cost = DEFAULT_SHIPPING_COST if cart_items else 0
    total_amount = subtotal + shipping_cost

    if request.method == 'POST':
        if not cart_items:
            messages.error(request, _('Your cart is empty.'))
            return redirect('store:cart-detail')

        selected_address_id = request.POST.get('shipping_address')
        if selected_address_id == 'new' or not selected_address_id:
            street = request.POST.get('street', '').strip()
            city = request.POST.get('city', '').strip()
            state = request.POST.get('state', '').strip()
            zip_code = request.POST.get('zip_code', '').strip()
            country = request.POST.get('country', '').strip()

            if not all([street, city, state, zip_code, country]):
                messages.error(
                    request,
                    _('Please complete all shipping address fields.'),
                )
                return redirect('store:checkout')

            address = Address.objects.create(
                user=request.user,
                street=street,
                city=city,
                state=state,
                zip_code=zip_code,
                country=country,
                is_default=(request.POST.get('set_default') == 'on'),
            )
            if address.is_default:
                Address.objects.filter(user=request.user).exclude(
                    id=address.id,
                ).update(is_default=False)
        else:
            address = get_object_or_404(
                Address,
                id=selected_address_id,
                user=request.user,
            )

        try:
            order = create_order_from_cart(
                user=request.user,
                shipping_address=address,
            )
        except ValidationError as error:
            messages.error(request, error.message)
            return redirect('store:checkout')

        messages.success(
            request,
            _('Order #%(order_id)s was created successfully.')
            % {'order_id': order.id},
        )
        return redirect('payments:create-payment', order_id=order.id)

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'addresses': addresses,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'total_amount': total_amount,
    }
    return render(request, 'store/checkout.html', context)
