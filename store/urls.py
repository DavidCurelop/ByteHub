from django.urls import path

from .views import product_list

app_name = 'store'

urlpatterns = [
    path('', product_list, name='product-list'),
]
