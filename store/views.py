from django.shortcuts import get_object_or_404, render

from .models import Product


def product_list(request):
    raw_search_query = request.GET.get('q', '')
    products = Product.objects.search_active_products_by_name(
        raw_search_query,
    )
    search_query = raw_search_query.strip()
    return render(
        request, 'store/product_list.html',
        {
            'products': products,
            'search_query': search_query,
            'is_searching': bool(search_query),
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.get_public_detail(),
        slug=slug,
    )
    context = {
        'product': product,
        'verified_reviews': product.verified_reviews,
        'average_rating': product.avg_rating(),
    }
    return render(request, 'store/product_detail.html', context)
