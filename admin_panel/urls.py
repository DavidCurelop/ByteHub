from django.urls import path

from .views import category_create, category_delete, category_edit, category_list

app_name = 'admin_panel'

urlpatterns = [
    path(
        'categories/',
        category_list,
        name='category-list',
    ),
    path(
        'categories/new/',
        category_create,
        name='category-create',
    ),
    path(
        'categories/<int:pk>/edit/',
        category_edit,
        name='category-edit',
    ),
    path(
        'categories/<int:pk>/delete/',
        category_delete,
        name='category-delete',
    ),
]
