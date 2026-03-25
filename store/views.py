from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from .models import Cart, CartItem, Product


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
    cart, _created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1},
    )

    if not item_created:
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
