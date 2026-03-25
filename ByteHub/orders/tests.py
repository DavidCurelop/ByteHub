from datetime import datetime, timezone
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import Address
from pages.models import Category
from store.models import Product

from .models import Cart, CartItem, Order, OrderItem, Payment
from .services import (
    ChargeResult,
    IInvoiceProvider,
    IPaymentProvider,
    PDFInvoiceProvider,
    StripePaymentProvider,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(email, **kwargs):
    defaults = {
        'password': 'StrongPass123',
        'first_name': 'Test',
        'last_name': 'User',
    }
    defaults.update(kwargs)
    return User.objects.create_user(email=email, **defaults)


def make_address(user, **kwargs):
    defaults = {
        'street': '123 Main St',
        'city': 'Springfield',
        'state': 'IL',
        'zip_code': '62701',
        'country': 'US',
    }
    defaults.update(kwargs)
    return Address.objects.create(user=user, **defaults)


def make_product(name, slug, admin_user, category, **kwargs):
    defaults = {
        'price': Decimal('10.00'),
        'stock': 100,
        'is_available': True,
    }
    defaults.update(kwargs)
    return Product.objects.create(
        name=name,
        slug=slug,
        category=category,
        created_by=admin_user,
        **defaults,
    )


# ---------------------------------------------------------------------------
# Address tests
# ---------------------------------------------------------------------------

class AddressModelTests(TestCase):
    """Tests for the Address model in the accounts app."""

    def setUp(self):
        self.user = make_user('addr@example.com')

    def test_address_str(self):
        addr = make_address(self.user)
        self.assertIn('123 Main St', str(addr))

    def test_address_is_default_false_by_default(self):
        addr = make_address(self.user)
        self.assertFalse(addr.is_default)

    def test_address_clean_strips_whitespace(self):
        addr = Address(
            user=self.user,
            street='  Elm Ave  ',
            city='  Shelbyville  ',
            state='  IL  ',
            zip_code='  62702  ',
            country='  US  ',
        )
        addr.clean()
        self.assertEqual(addr.street, 'Elm Ave')
        self.assertEqual(addr.city, 'Shelbyville')

    def test_address_clean_raises_on_blank_street(self):
        addr = Address(
            user=self.user,
            street='',
            city='Springfield',
            state='IL',
            zip_code='62701',
            country='US',
        )
        with self.assertRaises(ValidationError) as ctx:
            addr.clean()
        self.assertIn('street', ctx.exception.message_dict)

    def test_user_related_name_returns_addresses(self):
        make_address(self.user)
        make_address(self.user, street='456 Oak Ave')
        self.assertEqual(self.user.addresses.count(), 2)


# ---------------------------------------------------------------------------
# Cart / CartItem tests
# ---------------------------------------------------------------------------

class CartModelTests(TestCase):

    def setUp(self):
        self.admin = make_user('admin@example.com', is_admin=True)
        self.user = make_user('cart@example.com')
        self.category = Category.objects.create(
            name='Test Cat', slug='test-cat',
        )
        self.product_a = make_product(
            'Widget A', 'widget-a', self.admin, self.category,
            price=Decimal('5.00'),
        )
        self.product_b = make_product(
            'Widget B', 'widget-b', self.admin, self.category,
            price=Decimal('12.50'),
        )
        self.cart = Cart.objects.create(user=self.user)

    def test_cart_str(self):
        self.assertIn(str(self.user), str(self.cart))

    def test_get_total_empty_cart(self):
        self.assertEqual(self.cart.get_total(), Decimal('0.00'))

    def test_get_item_count_empty_cart(self):
        self.assertEqual(self.cart.get_item_count(), 0)

    def test_get_total_with_items(self):
        CartItem.objects.create(
            cart=self.cart, product=self.product_a, quantity=3,
        )
        CartItem.objects.create(
            cart=self.cart, product=self.product_b, quantity=2,
        )
        # 3*5 + 2*12.5 = 15 + 25 = 40
        self.assertEqual(self.cart.get_total(), Decimal('40.00'))

    def test_get_item_count_with_items(self):
        CartItem.objects.create(
            cart=self.cart, product=self.product_a, quantity=3,
        )
        CartItem.objects.create(
            cart=self.cart, product=self.product_b, quantity=2,
        )
        self.assertEqual(self.cart.get_item_count(), 5)

    def test_cart_item_get_subtotal(self):
        item = CartItem.objects.create(
            cart=self.cart, product=self.product_a, quantity=4,
        )
        self.assertEqual(item.get_subtotal(), Decimal('20.00'))

    def test_duplicate_cart_item_raises_integrity_error(self):
        CartItem.objects.create(
            cart=self.cart, product=self.product_a, quantity=1,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CartItem.objects.create(
                    cart=self.cart, product=self.product_a, quantity=2,
                )

    def test_cart_item_clean_raises_on_zero_quantity(self):
        item = CartItem(cart=self.cart, product=self.product_a, quantity=0)
        with self.assertRaises(ValidationError) as ctx:
            item.clean()
        self.assertIn('quantity', ctx.exception.message_dict)

    def test_cart_item_str(self):
        item = CartItem(
            cart=self.cart, product=self.product_a, quantity=2,
        )
        self.assertIn('2', str(item))
        self.assertIn(self.product_a.name, str(item))


# ---------------------------------------------------------------------------
# Order / OrderItem / Payment tests
# ---------------------------------------------------------------------------

class OrderModelTests(TestCase):

    def setUp(self):
        self.admin = make_user('oadmin@example.com', is_admin=True)
        self.user = make_user('order@example.com')
        self.address = make_address(self.user)
        self.category = Category.objects.create(
            name='Order Cat', slug='order-cat',
        )
        self.product = make_product(
            'Gadget', 'gadget', self.admin, self.category,
            price=Decimal('25.00'),
        )

    def _make_order(self, **kwargs):
        defaults = {
            'user': self.user,
            'shipping_address': self.address,
            'status': Order.STATUS_PENDING,
            'subtotal': Decimal('50.00'),
            'shipping_cost': Decimal('5.00'),
            'total_amount': Decimal('55.00'),
        }
        defaults.update(kwargs)
        return Order.objects.create(**defaults)

    def test_order_str(self):
        order = self._make_order()
        self.assertIn(str(self.user), str(order))

    def test_order_clean_valid_total(self):
        order = Order(
            user=self.user,
            shipping_address=self.address,
            subtotal=Decimal('100.00'),
            shipping_cost=Decimal('10.00'),
            total_amount=Decimal('110.00'),
        )
        # Should not raise
        order.clean()

    def test_order_clean_raises_on_mismatched_total(self):
        order = Order(
            user=self.user,
            shipping_address=self.address,
            subtotal=Decimal('100.00'),
            shipping_cost=Decimal('10.00'),
            total_amount=Decimal('999.00'),
        )
        with self.assertRaises(ValidationError) as ctx:
            order.clean()
        self.assertIn('total_amount', ctx.exception.message_dict)

    def test_order_item_get_subtotal(self):
        order = self._make_order()
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=3,
            unit_price=Decimal('25.00'),
        )
        self.assertEqual(item.get_subtotal(), Decimal('75.00'))

    def test_order_item_clean_raises_on_zero_quantity(self):
        order = self._make_order()
        item = OrderItem(
            order=order,
            product=self.product,
            quantity=0,
            unit_price=Decimal('25.00'),
        )
        with self.assertRaises(ValidationError) as ctx:
            item.clean()
        self.assertIn('quantity', ctx.exception.message_dict)

    def test_order_item_clean_raises_on_zero_price(self):
        order = self._make_order()
        item = OrderItem(
            order=order,
            product=self.product,
            quantity=1,
            unit_price=Decimal('0.00'),
        )
        with self.assertRaises(ValidationError) as ctx:
            item.clean()
        self.assertIn('unit_price', ctx.exception.message_dict)

    def test_order_item_str(self):
        order = self._make_order()
        item = OrderItem(
            order=order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('25.00'),
        )
        self.assertIn(self.product.name, str(item))

    def test_payment_str(self):
        order = self._make_order()
        payment = Payment(
            order=order,
            payment_method=Payment.METHOD_STRIPE,
            transaction_id='txn_abc123',
            status=Payment.STATUS_COMPLETED,
            amount=Decimal('55.00'),
        )
        self.assertIn('txn_abc123', str(payment))

    def test_payment_clean_raises_on_zero_amount(self):
        order = self._make_order()
        payment = Payment(
            order=order,
            payment_method=Payment.METHOD_STRIPE,
            transaction_id='txn_zero',
            amount=Decimal('0.00'),
        )
        with self.assertRaises(ValidationError) as ctx:
            payment.clean()
        self.assertIn('amount', ctx.exception.message_dict)


# ---------------------------------------------------------------------------
# OrderManager tests
# ---------------------------------------------------------------------------

class OrderManagerTests(TestCase):

    def setUp(self):
        self.admin = make_user('madmin@example.com', is_admin=True)
        self.user = make_user('manager@example.com')
        self.address = make_address(self.user)
        self.category = Category.objects.create(
            name='Mgr Cat', slug='mgr-cat',
        )
        self.product = make_product(
            'Mgr Prod', 'mgr-prod', self.admin, self.category,
        )

    def _create_order(self, user=None, **kwargs):
        u = user or self.user
        defaults = {
            'user': u,
            'shipping_address': self.address,
            'subtotal': Decimal('20.00'),
            'shipping_cost': Decimal('2.00'),
            'total_amount': Decimal('22.00'),
        }
        defaults.update(kwargs)
        return Order.objects.create(**defaults)

    def test_get_user_orders_with_details_returns_correct_user(self):
        self._create_order()
        other_user = make_user('other@example.com')
        other_addr = make_address(other_user)
        Order.objects.create(
            user=other_user,
            shipping_address=other_addr,
            subtotal=Decimal('5.00'),
            shipping_cost=Decimal('0.00'),
            total_amount=Decimal('5.00'),
        )
        qs = Order.objects.get_user_orders_with_details(self.user.pk)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().user, self.user)

    def test_get_user_orders_no_extra_queries(self):
        order = self._create_order()
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            unit_price=Decimal('20.00'),
        )
        qs = list(Order.objects.get_user_orders_with_details(self.user.pk))
        with self.assertNumQueries(0):
            for o in qs:
                _ = o.user.email
                for item in o.items.all():
                    _ = item.product.name

    def test_get_store_sales_summary_counts_and_sums(self):
        self._create_order(total_amount=Decimal('22.00'),
                           subtotal=Decimal('20.00'),
                           shipping_cost=Decimal('2.00'))
        self._create_order(total_amount=Decimal('33.00'),
                           subtotal=Decimal('30.00'),
                           shipping_cost=Decimal('3.00'))
        start = datetime(2000, 1, 1, tzinfo=timezone.utc)
        end = datetime(2099, 1, 1, tzinfo=timezone.utc)
        summary = Order.objects.get_store_sales_summary((start, end))
        self.assertEqual(summary['total_orders'], 2)
        self.assertEqual(summary['total_revenue'], Decimal('55.00'))

    def test_get_store_sales_summary_empty_range(self):
        start = datetime(2000, 1, 1, tzinfo=timezone.utc)
        end = datetime(2000, 1, 2, tzinfo=timezone.utc)
        summary = Order.objects.get_store_sales_summary((start, end))
        self.assertEqual(summary['total_orders'], 0)
        self.assertEqual(summary['total_revenue'], Decimal('0.00'))


# ---------------------------------------------------------------------------
# Service layer tests
# ---------------------------------------------------------------------------

class IPaymentProviderContractTests(TestCase):
    """Verify that IPaymentProvider cannot be instantiated directly."""

    def test_cannot_instantiate_abstract_class(self):
        with self.assertRaises(TypeError):
            IPaymentProvider()


class IInvoiceProviderContractTests(TestCase):
    """Verify that IInvoiceProvider cannot be instantiated directly."""

    def test_cannot_instantiate_abstract_class(self):
        with self.assertRaises(TypeError):
            IInvoiceProvider()


class StripePaymentProviderTests(TestCase):
    """Unit tests for StripePaymentProvider using a mock stripe module."""

    def _make_provider(self):
        return StripePaymentProvider(api_key='sk_test_fake')

    def test_implements_interface(self):
        provider = self._make_provider()
        self.assertIsInstance(provider, IPaymentProvider)

    def test_charge_raises_import_error_when_stripe_missing(self):
        import sys
        # Temporarily hide stripe if present
        stripe_mod = sys.modules.pop('stripe', None)
        try:
            provider = self._make_provider()
            with self.assertRaises(ImportError):
                provider.charge(Decimal('10.00'), 'pm_test')
        finally:
            if stripe_mod is not None:
                sys.modules['stripe'] = stripe_mod

    def test_charge_result_dataclass_fields(self):
        result = ChargeResult(
            success=True,
            transaction_id='txn_123',
            amount=Decimal('20.00'),
        )
        self.assertTrue(result.success)
        self.assertEqual(result.transaction_id, 'txn_123')
        self.assertIsNone(result.error_message)

    def test_charge_result_with_error(self):
        result = ChargeResult(
            success=False,
            transaction_id='',
            amount=Decimal('20.00'),
            error_message='Card declined',
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, 'Card declined')


class PDFInvoiceProviderTests(TestCase):
    """Unit tests for PDFInvoiceProvider."""

    def setUp(self):
        self.admin = make_user('pdf_admin@example.com', is_admin=True)
        self.user = make_user('pdf@example.com')
        self.address = make_address(self.user)
        self.category = Category.objects.create(
            name='PDF Cat', slug='pdf-cat',
        )
        self.product = make_product(
            'PDF Prod', 'pdf-prod', self.admin, self.category,
            price=Decimal('15.00'),
        )
        self.order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            subtotal=Decimal('30.00'),
            shipping_cost=Decimal('5.00'),
            total_amount=Decimal('35.00'),
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('15.00'),
        )

    def test_implements_interface(self):
        provider = PDFInvoiceProvider()
        self.assertIsInstance(provider, IInvoiceProvider)

    def test_generate_invoice_returns_bytes(self):
        provider = PDFInvoiceProvider()
        result = provider.generate_invoice(self.order)
        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), 0)

    def test_generate_invoice_text_fallback_contains_order_info(self):
        provider = PDFInvoiceProvider()
        # Force the text fallback by calling it directly
        result = provider._generate_text_fallback(self.order)
        text = result.decode('utf-8')
        self.assertIn(f'Order #{self.order.pk}', text)
        self.assertIn('PDF Prod', text)
        self.assertIn('35.00', text)
