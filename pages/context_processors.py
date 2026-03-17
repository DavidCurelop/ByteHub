from django.core.cache import cache
from .models import Category


def active_categories(request):
    """Provide active categories to all templates."""
    categories = cache.get_or_set(
        "active_categories",
        lambda: list(
            Category.objects.filter(is_active=True).only(
                "id",
                "name",
                "slug",
                "description",
            )
        ),
        60,
    )
    return {"categories": categories}
