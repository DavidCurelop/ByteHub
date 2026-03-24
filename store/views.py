from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .forms import CheckoutForm
from .models import Address, Cart, Order, Product
from .services import CartService


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
def add_to_cart(request, product_id):
    product = get_object_or_404(
        Product.objects.get_active_products(),
        pk=product_id,
    )

    raw_quantity = request.POST.get('quantity', '1')
    try:
        quantity = int(raw_quantity)
    except (TypeError, ValueError):
        messages.error(request, _('Invalid quantity.'))
        return redirect(request.POST.get('next', 'store:product-list'))

    try:
        _cart_item, is_new_item = CartService.add_product_for_user(
            user=request.user,
            product=product,
            quantity=quantity,
        )
    except ValidationError as error:
        for text in error.messages:
            messages.error(request, text)
    else:
        if is_new_item:
            messages.success(
                request,
                _('%(product)s was added to your cart.')
                % {'product': product.name},
            )
        else:
            messages.success(
                request,
                _('Your cart quantity for %(product)s was updated.')
                % {'product': product.name},
            )

    return redirect(request.POST.get('next', 'store:product-list'))


@login_required
def cart_detail(request):
    cart = Cart.objects.filter(user=request.user).first()

    if cart is None:
        context = {
            'cart': None,
            'items': [],
            'cart_total': 0,
            'item_count': 0,
        }
        return render(request, 'store/cart_detail.html', context)

    items = cart.items.select_related('product', 'product__category').all()
    context = {
        'cart': cart,
        'items': items,
        'cart_total': cart.get_total(),
        'item_count': cart.get_item_count(),
    }
    return render(request, 'store/cart_detail.html', context)


@login_required
@require_POST
def update_cart_item(request, item_id):
    raw_quantity = request.POST.get('quantity', '1')
    try:
        quantity = int(raw_quantity)
    except (TypeError, ValueError):
        messages.error(request, _('Invalid quantity.'))
        return redirect('store:cart-detail')

    try:
        item = CartService.update_item_quantity_for_user(
            user=request.user,
            cart_item_id=item_id,
            quantity=quantity,
        )
    except ValidationError as error:
        for text in error.messages:
            messages.error(request, text)
    else:
        messages.success(
            request,
            _('Quantity updated for %(product)s.')
            % {'product': item.product.name},
        )

    return redirect('store:cart-detail')


@login_required
@require_POST
def remove_cart_item(request, item_id):
    product_name = CartService.remove_item_for_user(
        user=request.user,
        cart_item_id=item_id,
    )
    messages.success(
        request,
        _('%(product)s was removed from your cart.')
        % {'product': product_name},
    )
    return redirect('store:cart-detail')


@login_required
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    if cart is None or not cart.items.exists():
        messages.error(request, _('Your cart is empty.'))
        return redirect('store:cart-detail')

    addresses = Address.objects.filter(user=request.user).order_by('-is_default')
    subtotal = cart.get_total()
    shipping_cost = CartService.SHIPPING_FLAT_RATE
    total_amount = subtotal + shipping_cost

    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                order = CartService.checkout_for_user(
                    user=request.user,
                    address_data=form.cleaned_data,
                )
            except ValidationError as error:
                for text in error.messages:
                    messages.error(request, text)
            else:
                messages.success(
                    request,
                    _('Your order was created successfully.'),
                )
                return redirect(
                    'store:order-success',
                    order_id=order.id,
                )
    else:
        initial = {
            'address_option': (
                CheckoutForm.ADDRESS_OPTION_EXISTING
                if addresses.exists()
                else CheckoutForm.ADDRESS_OPTION_NEW
            )
        }
        if addresses.exists():
            initial['address_id'] = addresses.first().id
        form = CheckoutForm(user=request.user, initial=initial)

    context = {
        'cart': cart,
        'items': cart.items.select_related('product').all(),
        'addresses': addresses,
        'form': form,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'total_amount': total_amount,
    }
    return render(request, 'store/checkout.html', context)


@login_required
def order_success(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('shipping_address').prefetch_related(
            'items__product',
        ),
        pk=order_id,
        user=request.user,
    )
    context = {
        'order': order,
        'items': order.items.select_related('product').all(),
    }
    return render(request, 'store/order_success.html', context)
