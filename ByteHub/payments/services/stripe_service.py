import os
import stripe 

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(order):
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

        success_url='http://localhost:8000/payments/success/',
        cancel_url='http://localhost:8000/payments/cancel/',
    )

    return session