from django.urls import path

from .views import generate_invoice, order_detail, order_list

app_name = 'orders'

urlpatterns = [
    path('', order_list, name='order-list'),
    path('<int:pk>/', order_detail, name='order-detail'),
    path('<int:pk>/invoice/', generate_invoice, name='generate-invoice'),
]
