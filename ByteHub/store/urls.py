from django.urls import path

from .views import (
    add_to_cart,
    cart_detail,
    checkout,
    create_review_view,
    delete_cart_item_view,
    product_detail,
    product_list,
    product_list_by_category,
    update_cart_item,
)

app_name = 'store'

urlpatterns = [
    path('', product_list, name='product-list'),
    path('category/<slug:slug>/', product_list_by_category, name='product-list-by-category'),
    path('cart/', cart_detail, name='cart-detail'),
    path('checkout/', checkout, name='checkout'),
    path('cart/items/<int:item_id>/update/', update_cart_item, name='update-cart-item'),
    path('cart/items/<int:item_id>/delete/', delete_cart_item_view, name='delete-cart-item'),
    path('<slug:slug>/add-to-cart/', add_to_cart, name='add-to-cart'),
    path('<slug:slug>/reviews/add/', create_review_view, name='add-review'),
    path('<slug:slug>/', product_detail, name='product-detail'),
]
