from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render

from .models import Product, Review


def product_list(request):
    products = Product.objects.get_active_products()
    return render(
        request, 'store/product_list.html',
        {'products': products},
    )


def product_detail(request, slug):
    product_queryset = Product.objects.select_related('category').prefetch_related(
        Prefetch(
            'reviews',
            queryset=Review.objects.filter(
                is_verified_purchase=True,
            ).select_related('user'),
            to_attr='verified_reviews',
        )
    )
    product = get_object_or_404(
        product_queryset,
        slug=slug,
        is_available=True,
    )

    context = {
        'product': product,
        'verified_reviews': product.verified_reviews,
        'average_rating': product.avg_rating(),
    }
    return render(request, 'products/detail.html', context)
