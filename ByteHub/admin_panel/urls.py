from django.urls import path

from .views import (
    product_create,
    product_deactivate,
    product_edit,
    product_list,
)

app_name = 'admin_panel'

urlpatterns = [
    path(
        'products/',
        product_list,
        name='product-list',
    ),
    path(
        'products/create/',
        product_create,
        name='product-create',
    ),
    path(
        'products/<int:pk>/edit/',
        product_edit,
        name='product-edit',
    ),
    path(
        'products/<int:pk>/deactivate/',
        product_deactivate,
        name='product-deactivate',
    ),
]
