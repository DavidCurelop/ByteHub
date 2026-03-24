from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, F, Prefetch, Q, Sum
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

from pages.models import Category


class ProductManager(models.Manager):
    """Custom manager with reusable product queries."""

    def get_active_products(self):
        return (
            self.filter(is_available=True)
            .select_related('category')
        )

    def search_active_products_by_name(self, query):
        """Return active products filtered by a case-insensitive name."""
        cleaned_query = query.strip()
        if not cleaned_query:
            return self.get_active_products()
        return self.get_active_products().filter(name__icontains=cleaned_query)

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
        """Return average rating from verified reviews as a float.

        Uses the pre-annotated ``verified_avg_rating`` value when the
        object was fetched via ``get_public_detail()`` to avoid an
        extra aggregate query.
        """
        if hasattr(self, 'verified_avg_rating'):
            value = self.verified_avg_rating
        else:
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


class Cart(models.Model):
    """Shopping cart owned by an authenticated customer."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name=_('user'),
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
    )

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('cart')
        verbose_name_plural = _('carts')

    def __str__(self):
        return f'Cart #{self.pk} - user #{self.user_id}'

    def get_total(self):
        total = self.items.select_related('product').aggregate(
            total=Coalesce(Sum(F('quantity') * F('product__price')), Decimal('0.00')),
        )
        return total['total']

    def get_item_count(self):
        quantity = self.items.aggregate(
            quantity=Coalesce(Sum('quantity'), 0),
        )
        return int(quantity['quantity'])


class CartItem(models.Model):
    """Single line item for one product inside a cart."""

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('cart'),
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_('product'),
    )
    quantity = models.PositiveIntegerField(_('quantity'), default=1)

    class Meta:
        verbose_name = _('cart item')
        verbose_name_plural = _('cart items')
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'],
                name='store_cart_item_unique_cart_product',
            )
        ]

    def clean(self):
        super().clean()
        if self.quantity < 1:
            raise ValidationError(
                {'quantity': _('Quantity must be greater than zero.')},
            )
        if self.product_id and self.quantity > self.product.stock:
            raise ValidationError(
                {
                    'quantity': _(
                        'Requested quantity exceeds available stock.',
                    )
                },
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def get_subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f'Cart #{self.cart_id} - product #{self.product_id}'


class Address(models.Model):
    """Shipping address owned by a customer."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name=_('user'),
    )
    street = models.CharField(_('street'), max_length=255)
    city = models.CharField(_('city'), max_length=120)
    state = models.CharField(_('state'), max_length=120)
    zip_code = models.CharField(_('zip code'), max_length=20)
    country = models.CharField(_('country'), max_length=120)
    is_default = models.BooleanField(_('default address'), default=False)

    class Meta:
        ordering = ['-is_default', '-id']
        verbose_name = _('address')
        verbose_name_plural = _('addresses')

    def __str__(self):
        return (
            f'{self.street}, {self.city}, {self.state}, '
            f'{self.zip_code}, {self.country}'
        )


class Order(models.Model):
    """Confirmed order created from a cart checkout."""

    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'

    STATUS_CHOICES = (
        (STATUS_PENDING, _('Pending')),
        (STATUS_PAID, _('Paid')),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('user'),
    )
    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        related_name='shipping_orders',
        verbose_name=_('shipping address'),
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    subtotal = models.DecimalField(
        _('subtotal'),
        max_digits=10,
        decimal_places=2,
    )
    shipping_cost = models.DecimalField(
        _('shipping cost'),
        max_digits=10,
        decimal_places=2,
    )
    total_amount = models.DecimalField(
        _('total amount'),
        max_digits=10,
        decimal_places=2,
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('order')
        verbose_name_plural = _('orders')

    def __str__(self):
        return f'Order #{self.pk}'


class OrderItem(models.Model):
    """Snapshot of a purchased product line for an order."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('order'),
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name=_('product'),
    )
    quantity = models.PositiveIntegerField(_('quantity'))
    unit_price = models.DecimalField(
        _('unit price'),
        max_digits=10,
        decimal_places=2,
    )

    class Meta:
        verbose_name = _('order item')
        verbose_name_plural = _('order items')

    def get_subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f'Order #{self.order_id} - product #{self.product_id}'
