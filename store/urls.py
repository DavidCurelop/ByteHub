from django.urls import path

from .views import product_detail, product_list

app_name = 'store'

urlpatterns = [
    path('', product_list, name='product-list'),
    path('<slug:slug>/', product_detail, name='product-detail'),
]
