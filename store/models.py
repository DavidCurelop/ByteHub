from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Prefetch, Q
from django.utils.translation import gettext_lazy as _

from pages.models import Category


class ProductManager(models.Manager):
    """Custom manager with reusable product queries."""

    def get_active_products(self):
        return (
            self.filter(is_available=True)
            .select_related('category')
        )

    def get_products_by_category(self, category_slug):
        return (
            self.filter(
                is_available=True,
                category__slug=category_slug,
            )
            .select_related('category')
        )

    def get_products_managed_by(self, admin_id):
        return (
            self.filter(created_by_id=admin_id)
            .select_related('category', 'created_by')
        )

    def get_public_detail(self):
        """Return optimized queryset for public product detail pages."""
        return (
            self.filter(is_available=True)
            .select_related('category')
            .prefetch_related(
                Prefetch(
                    'reviews',
                    queryset=Review.objects.filter(
                        is_verified_purchase=True,
                    ).select_related('user'),
                    to_attr='verified_reviews',
                )
            )
            .annotate(
                verified_avg_rating=Avg(
                    'reviews__rating',
                    filter=Q(reviews__is_verified_purchase=True),
                )
            )
        )


class Product(models.Model):
    """Product available in the store."""

    name = models.CharField(_('name'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=220, unique=True)
    description = models.TextField(_('description'), blank=True)
    brand = models.CharField(_('brand'), max_length=100, blank=True)
    price = models.DecimalField(
        _('price'), max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    stock = models.PositiveIntegerField(_('stock'), default=0)
    image = models.URLField(
        _('image'), max_length=500, blank=True,
    )
    is_available = models.BooleanField(_('available'), default=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name=_('category'),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='managed_products',
        verbose_name=_('created by'),
    )
    created_at = models.DateTimeField(
        _('created at'), auto_now_add=True,
    )

    objects = ProductManager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('product')
        verbose_name_plural = _('products')

    def clean(self):
        super().clean()
        if self.price is not None and self.price <= 0:
            raise ValidationError(
                {'price': _("Price must be greater than zero.")}
            )

    def __str__(self):
        return self.name

    def avg_rating(self):
        """Return average rating from verified reviews as a float."""
        result = self.reviews.filter(
            is_verified_purchase=True,
        ).aggregate(average=Avg('rating'))
        value = result['average']
        return float(value) if value is not None else 0.0


class Review(models.Model):
    """Verified or unverified customer review for a product."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('product'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('user'),
    )
    rating = models.PositiveSmallIntegerField(
        _('rating'),
        validators=[
            MinValueValidator(
                1, message=_("Rating must be between 1 and 5."),
            ),
            MaxValueValidator(
                5, message=_("Rating must be between 1 and 5."),
            ),
        ],
    )
    title = models.CharField(_('title'), max_length=120, blank=True)
    body = models.TextField(_('review body'), blank=True)
    is_verified_purchase = models.BooleanField(
        _('verified purchase'), default=False,
    )
    created_at = models.DateTimeField(
        _('created at'), auto_now_add=True,
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('review')
        verbose_name_plural = _('reviews')
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'user'],
                name='store_review_unique_product_user',
            )
        ]

    def __str__(self):
        return f'Product #{self.product_id} - {self.rating}'
