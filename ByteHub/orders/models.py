from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

from store.models import Product


class OrderManager(models.Manager):
    """Custom manager with reusable order queries."""

    def get_user_orders_with_details(self, user_id):
        """Return orders for a user with items and products prefetched."""
        return (
            self.filter(user_id=user_id)
            .prefetch_related(
                Prefetch(
                    'items',
                    queryset=OrderItem.objects.select_related('product'),
                )
            )
            .order_by('-created_at')
        )


STATUS_PENDING = 'pending'
STATUS_CONFIRMED = 'confirmed'
STATUS_SHIPPED = 'shipped'
STATUS_DELIVERED = 'delivered'
STATUS_CANCELLED = 'cancelled'

ORDER_STATUS_CHOICES = [
    (STATUS_PENDING, _('Pending')),
    (STATUS_CONFIRMED, _('Confirmed')),
    (STATUS_SHIPPED, _('Shipped')),
    (STATUS_DELIVERED, _('Delivered')),
    (STATUS_CANCELLED, _('Cancelled')),
]


class Order(models.Model):
    """A purchase order placed by a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name=_('user'),
    )
    shipping_address = models.TextField(
        _('shipping address'), blank=True,
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    subtotal = models.DecimalField(
        _('subtotal'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    shipping_cost = models.DecimalField(
        _('shipping cost'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    total_amount = models.DecimalField(
        _('total amount'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    created_at = models.DateTimeField(
        _('created at'), auto_now_add=True,
    )

    objects = OrderManager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('order')
        verbose_name_plural = _('orders')

    def __str__(self):
        return f'Order #{self.pk} — {self.user}'

    def clean(self):
        super().clean()
        expected_total = (self.subtotal or Decimal('0.00')) + (
            self.shipping_cost or Decimal('0.00')
        )
        if (
            self.total_amount is not None
            and self.total_amount != expected_total
        ):
            raise ValidationError(
                {
                    'total_amount': _(
                        'Total amount must equal subtotal plus '
                        'shipping cost.'
                    )
                }
            )


class OrderItem(models.Model):
    """A single line item within an order."""

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
    quantity = models.PositiveIntegerField(
        _('quantity'),
        validators=[MinValueValidator(1)],
    )
    unit_price = models.DecimalField(
        _('unit price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )

    class Meta:
        verbose_name = _('order item')
        verbose_name_plural = _('order items')

    def __str__(self):
        return f'{self.quantity}× {self.product}'

    def get_subtotal(self):
        """Return line total as unit_price × quantity."""
        return self.unit_price * self.quantity
