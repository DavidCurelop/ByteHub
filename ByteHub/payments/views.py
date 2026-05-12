from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from store.models import Order

# Create your views here.
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from store.models import Order
from .services.stripe_service import create_checkout_session


@login_required
def create_payment(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
    )

    checkout_session = create_checkout_session(order)

    return redirect(checkout_session.url)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            endpoint_secret
        )
    except Exception:
        return HttpResponse(status=400)

    # Evento de pago exitoso
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Aquí luego conectamos con Order real
        print("Pago confirmado:", session['id'])

    return HttpResponse(status=200)

def payment_success(request):
    return render(request, 'payments/success.html')

def payment_cancel(request):
    return render(request, 'payments/cancel.html')