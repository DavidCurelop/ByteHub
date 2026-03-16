from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
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
            .select_related('category')
        )


class Product(models.Model):
    """Product available in the store."""

    name = models.CharField(_('name'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=220, unique=True)
    description = models.TextField(_('description'), blank=True)
    brand = models.CharField(_('brand'), max_length=100, blank=True)
    price = models.DecimalField(
        _('price'), max_digits=10, decimal_places=2,
    )
    stock = models.IntegerField(_('stock'), default=0)
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

    def __str__(self):
        return self.name

    def clean(self):
        errors = {}

        if self.price is not None and self.price <= 0:
            errors['price'] = _(
                'Price must be greater than zero.'
            )

        if self.stock is not None and self.stock < 0:
            errors['stock'] = _(
                'Stock cannot be negative.'
            )

        if errors:
            raise ValidationError(errors)
