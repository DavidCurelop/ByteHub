from django.urls import path
from .views import create_payment, payment_cancel, payment_cancel, payment_success, stripe_webhook

app_name = 'payments'

urlpatterns = [
    path(
        'create/<int:order_id>/',
        create_payment,
        name='create-payment',
    ),
    path('success/', payment_success, name='payment-success'),
    path('cancel/', payment_cancel, name='payment-cancel'),
    path('webhook/', stripe_webhook, name='stripe-webhook'),
]