import os
import stripe
from django.urls import reverse

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(order, request):
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],

        line_items=[
            {
                'price_data': {
                    'currency': 'usd',

                    'product_data': {
                        'name': f'Order #{order.id}',
                    },

                    'unit_amount': int(order.total_amount * 100),
                },

                'quantity': 1,
            }
        ],

        mode='payment',

        success_url=request.build_absolute_uri(reverse('payments:payment-success')),
        cancel_url=request.build_absolute_uri(reverse('payments:payment-cancel')),
    )

    order.stripe_session_id = session.id
    order.save()

    return session