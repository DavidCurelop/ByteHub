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
    cart = Cart.objects.filter(user=request.user).prefetch_related(
        'items__product',
    ).first()
    cart_items = cart.items.all() if cart else []
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'store/cart_detail.html', context)
