from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from store.models import Product


class OrderManager(models.Manager):
    """Custom manager with reusable order queries."""

    def get_user_orders_with_details(self, user_id):
        return (
            self.filter(user_id=user_id)
            .select_related('user', 'shipping_address')
            .prefetch_related(
                models.Prefetch(
                    'items',
                    queryset=OrderItem.objects.select_related('product'),
                )
            )
            .order_by('-created_at')
        )


class Address(models.Model):
    """Shipping or billing address for a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name=_('user'),
    )
    street = models.CharField(_('street'), max_length=255)
    city = models.CharField(_('city'), max_length=100)
    state = models.CharField(_('state'), max_length=100)
    zip_code = models.CharField(_('zip code'), max_length=20)
    country = models.CharField(_('country'), max_length=100)
    is_default = models.BooleanField(_('default address'), default=False)

    class Meta:
        verbose_name = _('address')
        verbose_name_plural = _('addresses')

    def __str__(self):
        return f'{self.street}, {self.city}, {self.state} {self.zip_code}'

    def clean(self):
        super().clean()
        for field_name in ('street', 'city', 'state', 'zip_code', 'country'):
            value = getattr(self, field_name, '') or ''
            setattr(self, field_name, value.strip())


class Order(models.Model):
    """A customer order."""

    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_PROCESSING, _('Processing')),
        (STATUS_SHIPPED, _('Shipped')),
        (STATUS_DELIVERED, _('Delivered')),
        (STATUS_CANCELLED, _('Cancelled')),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name=_('user'),
    )
    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name=_('shipping address'),
        null=True,
        blank=True,
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
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    objects = OrderManager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('order')
        verbose_name_plural = _('orders')

    def __str__(self):
        return f'Order #{self.pk} – {self.user}'

    def clean(self):
        super().clean()
        if (
            self.subtotal is not None
            and self.shipping_cost is not None
            and self.total_amount is not None
        ):
            expected = self.subtotal + self.shipping_cost
            if self.total_amount != expected:
                raise ValidationError(
                    {
                        'total_amount': _(
                            'Total amount must equal subtotal plus'
                            ' shipping cost.'
                        )
                    }
                )

    @property
    def is_paid(self):
        """Return True if the linked payment is completed."""
        try:
            return self.payment.status == Payment.STATUS_COMPLETED
        except Payment.DoesNotExist:
            return False


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
    quantity = models.PositiveIntegerField(_('quantity'), default=1)
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
        return f'#{self.pk} – {self.product} x{self.quantity}'

    def clean(self):
        super().clean()
        if self.quantity is not None and self.quantity < 1:
            raise ValidationError(
                {'quantity': _('Quantity must be at least 1.')}
            )

    def get_subtotal(self):
        """Return line total (unit price × quantity)."""
        if self.unit_price is None or self.quantity is None:
            return Decimal('0.00')
        return self.unit_price * self.quantity


class Payment(models.Model):
    """Payment record associated with an order."""

    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'

    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_COMPLETED, _('Completed')),
        (STATUS_FAILED, _('Failed')),
        (STATUS_REFUNDED, _('Refunded')),
    ]

    METHOD_CARD = 'card'
    METHOD_PAYPAL = 'paypal'
    METHOD_TRANSFER = 'transfer'

    METHOD_CHOICES = [
        (METHOD_CARD, _('Credit/Debit Card')),
        (METHOD_PAYPAL, _('PayPal')),
        (METHOD_TRANSFER, _('Bank Transfer')),
    ]

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name=_('order'),
    )
    payment_method = models.CharField(
        _('payment method'),
        max_length=20,
        choices=METHOD_CHOICES,
    )
    transaction_id = models.CharField(
        _('transaction id'), max_length=255, blank=True,
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    amount = models.DecimalField(
        _('amount'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    paid_at = models.DateTimeField(_('paid at'), null=True, blank=True)

    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')

    def __str__(self):
        return f'Payment #{self.pk} for Order #{self.order_id}'
