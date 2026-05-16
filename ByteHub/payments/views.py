from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from store.models import Order
import os
import stripe
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
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    print("SIGNATURE HEADER:", sig_header)
    print("SECRET LOADED:", endpoint_secret is not None)

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            endpoint_secret
        )
    except Exception as e:
        print("WEBHOOK ERROR:", str(e))
        return HttpResponse(status=400)

    print("EVENT TYPE:", event["type"])

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        print("Session ID:", session["id"])

        order = Order.objects.filter(stripe_session_id=session["id"]).first()

        if order:
            order.status = "paid"
            order.save()

            print(f"Order {order.id} Marked as paid")
        else:
            print("Order not found")
    return HttpResponse(status=200)

def payment_success(request):
    return render(request, 'payments/success.html')

def payment_cancel(request):
    return render(request, 'payments/cancel.html')