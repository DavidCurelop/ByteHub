from django.urls import path

from .views import (
    add_to_cart,
    cart_detail,
    checkout,
    order_success,
    product_detail,
    product_list,
    remove_cart_item,
    update_cart_item,
)

app_name = 'store'

urlpatterns = [
    path('', product_list, name='product-list'),
    path('cart/', cart_detail, name='cart-detail'),
    path('checkout/', checkout, name='checkout'),
    path('orders/<int:order_id>/success/', order_success, name='order-success'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add-to-cart'),
    path(
        'cart/items/<int:item_id>/update/',
        update_cart_item,
        name='update-cart-item',
    ),
    path(
        'cart/items/<int:item_id>/remove/',
        remove_cart_item,
        name='remove-cart-item',
    ),
    path('<slug:slug>/', product_detail, name='product-detail'),
]
