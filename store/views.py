from django.shortcuts import render

from .models import Product


def product_list(request):
    products = Product.objects.get_active_products_with_reviews()
    return render(
        request, 'store/product_list.html',
        {'products': products},
    )
