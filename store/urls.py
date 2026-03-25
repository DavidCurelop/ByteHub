from django.urls import path

from .views import add_to_cart, cart_detail, product_detail, product_list

app_name = 'store'

urlpatterns = [
    path('', product_list, name='product-list'),
    path('cart/', cart_detail, name='cart-detail'),
    path('<slug:slug>/add-to-cart/', add_to_cart, name='add-to-cart'),
    path('<slug:slug>/', product_detail, name='product-detail'),
]
