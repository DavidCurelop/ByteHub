from django.shortcuts import render

from .models import Product, Category


def product_list(request):
    products = Product.objects.get_active_products()
    categories = Category.objects.filter(is_active=True)
    return render(
        request, 'store/product_list.html',
        {
            'products': products,
            'categories': categories,
        },
    )
