from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from store.models import Product


class OrderManager(models.Manager):
    """Custom manager for Order with reusable query helpers."""

    def get_user_orders_with_details(self, user_id):
        """Return all orders for a user, prefetching items and products."""
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

    def get_store_sales_summary(self, date_range):
        """Return a dict with total_orders and total_revenue for a date range.

        ``date_range`` is expected to be a tuple/list of two ``datetime``
        objects: ``(start, end)``.
        """
        start, end = date_range
        qs = self.filter(created_at__range=(start, end))
        total_orders = qs.count()
        total_revenue = (
            qs.aggregate(revenue=Sum('total_amount'))['revenue']
            or Decimal('0.00')
        )
        return {
            'total_orders': total_orders,
            'total_revenue': total_revenue,
        }


class Cart(models.Model):
    """Shopping cart associated with a single user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name=_('user'),
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('cart')
        verbose_name_plural = _('carts')

    def __str__(self):
        return f'Cart #{self.pk} – {self.user}'

    def clean(self):
        pass

    def get_total(self):
        """Return the sum of all cart item subtotals as a Decimal."""
        return sum(
            (item.get_subtotal() for item in self.cart_items.all()),
            Decimal('0.00'),
        )

    def get_item_count(self):
        """Return the total number of individual units in the cart."""
        return sum(item.quantity for item in self.cart_items.all())


class CartItem(models.Model):
    """A single product line inside a Cart."""

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_('cart'),
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_('product'),
    )
    quantity = models.PositiveIntegerField(
        _('quantity'),
        default=1,
        validators=[MinValueValidator(1)],
    )

    class Meta:
        verbose_name = _('cart item')
        verbose_name_plural = _('cart items')
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'],
                name='orders_cartitem_unique_cart_product',
            )
        ]

    def __str__(self):
        return f'{self.quantity} × {self.product}'

    def clean(self):
        if self.quantity is not None and self.quantity < 1:
            raise ValidationError(
                {'quantity': _('Quantity must be at least 1.')}
            )

    def get_subtotal(self):
        """Return line total as price × quantity."""
        return self.product.price * self.quantity


class Order(models.Model):
    """A confirmed purchase placed by a user."""

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
        'accounts.Address',
        on_delete=models.PROTECT,
        related_name='orders',
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
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    shipping_cost = models.DecimalField(
        _('shipping cost'),
        max_digits=8,
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
        errors = {}
        if (
            self.subtotal is not None
            and self.shipping_cost is not None
            and self.total_amount is not None
        ):
            expected_total = self.subtotal + self.shipping_cost
            if self.total_amount != expected_total:
                errors['total_amount'] = _(
                    'Total amount must equal subtotal plus shipping cost.'
                )
        if errors:
            raise ValidationError(errors)


class OrderItem(models.Model):
    """A single product line inside an Order."""

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
        return f'{self.quantity} × {self.product} (Order #{self.order_id})'

    def clean(self):
        errors = {}
        if self.quantity is not None and self.quantity < 1:
            errors['quantity'] = _('Quantity must be at least 1.')
        if self.unit_price is not None and self.unit_price <= 0:
            errors['unit_price'] = _('Unit price must be greater than zero.')
        if errors:
            raise ValidationError(errors)

    def get_subtotal(self):
        """Return line total as unit_price × quantity."""
        return self.unit_price * self.quantity


class Payment(models.Model):
    """Record of a payment transaction associated with an Order."""

    METHOD_CREDIT_CARD = 'credit_card'
    METHOD_DEBIT_CARD = 'debit_card'
    METHOD_PAYPAL = 'paypal'
    METHOD_STRIPE = 'stripe'
    METHOD_BANK_TRANSFER = 'bank_transfer'

    METHOD_CHOICES = [
        (METHOD_CREDIT_CARD, _('Credit Card')),
        (METHOD_DEBIT_CARD, _('Debit Card')),
        (METHOD_PAYPAL, _('PayPal')),
        (METHOD_STRIPE, _('Stripe')),
        (METHOD_BANK_TRANSFER, _('Bank Transfer')),
    ]

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

    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name='payment',
        verbose_name=_('order'),
    )
    payment_method = models.CharField(
        _('payment method'),
        max_length=30,
        choices=METHOD_CHOICES,
    )
    transaction_id = models.CharField(
        _('transaction ID'),
        max_length=255,
        unique=True,
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    paid_at = models.DateTimeField(_('paid at'), null=True, blank=True)
    amount = models.DecimalField(
        _('amount'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )

    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')

    def __str__(self):
        return (
            f'Payment {self.transaction_id} – '
            f'{self.get_status_display()} ({self.amount})'
        )

    def clean(self):
        errors = {}
        if self.amount is not None and self.amount <= 0:
            errors['amount'] = _('Amount must be greater than zero.')
        if errors:
            raise ValidationError(errors)
