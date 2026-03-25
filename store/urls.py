from django.urls import path

from .views import (
    add_to_cart,
    cart_detail,
    checkout,
    delete_cart_item,
    product_detail,
    product_list,
    update_cart_item,
)

app_name = 'store'

urlpatterns = [
    path('', product_list, name='product-list'),
    path('cart/', cart_detail, name='cart-detail'),
    path('checkout/', checkout, name='checkout'),
    path('cart/items/<int:item_id>/update/', update_cart_item, name='update-cart-item'),
    path('cart/items/<int:item_id>/delete/', delete_cart_item, name='delete-cart-item'),
    path('<slug:slug>/add-to-cart/', add_to_cart, name='add-to-cart'),
    path('<slug:slug>/', product_detail, name='product-detail'),
]
