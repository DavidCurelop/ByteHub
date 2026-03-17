from .models import Category


def active_categories(request):
    """Provide active categories to all templates."""
    return {'categories': Category.objects.filter(is_active=True)}
