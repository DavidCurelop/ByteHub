from django.shortcuts import get_object_or_404, render

from .models import Product


def product_list(request):
    products = Product.objects.get_active_products()
    return render(
        request, 'store/product_list.html',
        {'products': products},
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.get_public_detail(),
        slug=slug,
    )
    average_rating = product.verified_avg_rating or 0.0
    context = {
        'product': product,
        'verified_reviews': product.verified_reviews,
        'average_rating': average_rating,
    }
    return render(request, 'store/product_detail.html', context)
