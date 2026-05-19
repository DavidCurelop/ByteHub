import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from orders.services import create_order_from_cart
from pages.models import Category
from .forms import ReviewForm
from .models import Address, Order, OrderItem, Product
from .services import (
    add_product_to_cart,
    compute_checkout_summary,
    create_review,
    delete_cart_item,
    resolve_shipping_address,
    update_cart_item_quantity,
)


def product_list(request):
    raw_search_query = request.GET.get('q', '')
    products = Product.objects.search_active_products_by_name(raw_search_query)
    search_query = raw_search_query.strip()
    return render(
        request, 'store/product_list.html',
        {
            'products': products,
            'search_query': search_query,
            'is_searching': bool(search_query),
        },
    )


def product_list_by_category(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.get_products_by_category(slug)
    raw_search_query = request.GET.get('q', '')
    search_query = raw_search_query.strip()
    if search_query:
        products = products.filter(name__icontains=search_query)
    return render(
        request, 'store/product_list.html',
        {
            'products': products,
            'current_category': category,
            'search_query': search_query,
            'is_searching': bool(search_query),
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.get_public_detail(),
        slug=slug,
    )
    has_purchased = False
    if request.user.is_authenticated:
        has_purchased = OrderItem.objects.filter(
            product=product,
            order__user=request.user,
            order__status=Order.STATUS_CONFIRMED,
        ).exists()
    context = {
        'product': product,
        'verified_reviews': product.verified_reviews,
        'average_rating': product.avg_rating(),
        'has_purchased': has_purchased,
    }
    if request.user.is_authenticated:
        context['review_form'] = ReviewForm()
    return render(request, 'store/product_detail.html', context)


@login_required
@require_POST
def add_to_cart(request, slug):
    try:
        add_product_to_cart(user=request.user, product_slug=slug)
    except ObjectDoesNotExist:
        raise Http404
    except ValidationError as error:
        messages.error(request, error.message)
        return redirect('store:product-detail', slug=slug)

    messages.success(request, _('Product added to your cart.'))
    return redirect('store:product-detail', slug=slug)


@login_required
def cart_detail(request):
    cart, cart_items, *_ = compute_checkout_summary(request.user)
    return render(
        request, 'store/cart_detail.html',
        {'cart': cart, 'cart_items': cart_items},
    )


@login_required
@require_POST
def update_cart_item(request, item_id):
    try:
        quantity = int(request.POST.get('quantity', '1'))
    except ValueError:
        quantity = 1

    try:
        update_cart_item_quantity(
            user=request.user, item_id=item_id, quantity=quantity,
        )
    except ObjectDoesNotExist:
        raise Http404
    except ValidationError as error:
        messages.error(request, error.message)
        return redirect('store:cart-detail')

    messages.success(request, _('Cart item quantity updated.'))
    return redirect('store:cart-detail')


@login_required
@require_POST
def delete_cart_item_view(request, item_id):
    try:
        delete_cart_item(user=request.user, item_id=item_id)
    except ObjectDoesNotExist:
        raise Http404
    messages.success(request, _('Item removed from your cart.'))
    return redirect('store:cart-detail')


@login_required
@require_POST
def create_review_view(request, slug):
    form = ReviewForm(request.POST)
    if not form.is_valid():
        messages.error(request, _('Please correct the errors in the review form.'))
        return redirect('store:product-detail', slug=slug)

    try:
        create_review(
            user=request.user,
            product_slug=slug,
            rating=form.cleaned_data['rating'],
            title=form.cleaned_data['title'],
            body=form.cleaned_data['body'],
        )
    except ObjectDoesNotExist:
        raise Http404
    except ValidationError as error:
        messages.error(request, error.message)
        return redirect('store:product-detail', slug=slug)
    except IntegrityError:
        messages.error(request, _('You have already reviewed this product.'))
        return redirect('store:product-detail', slug=slug)

    messages.success(request, _('Your review has been published.'))
    return redirect('store:product-detail', slug=slug)


@login_required
def checkout(request):
    cart, cart_items, subtotal, shipping_cost, total_amount = (
        compute_checkout_summary(request.user)
    )

    if request.method == 'POST':
        if not cart_items:
            messages.error(request, _('Your cart is empty.'))
            return redirect('store:cart-detail')

        try:
            address = resolve_shipping_address(
                user=request.user,
                selected_address_id=request.POST.get('shipping_address'),
                address_data=request.POST,
            )
        except ObjectDoesNotExist:
            raise Http404
        except ValidationError as error:
            messages.error(request, error.message)
            return redirect('store:checkout')

        try:
            order = create_order_from_cart(
                user=request.user, shipping_address=address,
            )
        except ValidationError as error:
            messages.error(request, error.message)
            return redirect('store:checkout')

        return redirect('payments:create-payment', order_id=order.id)

    addresses = Address.objects.filter(user=request.user)
    return render(
        request, 'store/checkout.html',
        {
            'cart': cart,
            'cart_items': cart_items,
            'addresses': addresses,
            'subtotal': subtotal,
            'shipping_cost': shipping_cost,
            'total_amount': total_amount,
            'google_maps_api_key': os.getenv('GOOGLE_MAPS_API_KEY', ''),
        },
    )