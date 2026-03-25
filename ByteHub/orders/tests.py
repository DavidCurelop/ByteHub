from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from pages.models import Category
from store.models import Product

from .models import (
    PAYMENT_STATUS_FAILED,
    PAYMENT_STATUS_SUCCEEDED,
    STATUS_PAID,
    STATUS_PENDING,
    Order,
    OrderItem,
    Payment,
)
from .services.payment_providers import PaymentResult

User = get_user_model()


def _make_user(email, **kwargs):
    return User.objects.create_user(
        email=email,
        password='StrongPass123',
        first_name='Test',
        last_name='User',
        **kwargs,
    )


def _make_product(name, category, admin):
    return Product.objects.create(
        name=name,
        slug=name.lower().replace(' ', '-'),
        price=Decimal('9.99'),
        stock=10,
        is_available=True,
        category=category,
        created_by=admin,
    )


def _make_order(user, status='pending', total=Decimal('29.99')):
    return Order.objects.create(
        user=user,
        status=status,
        subtotal=total,
        shipping_cost=Decimal('0.00'),
        total_amount=total,
    )


class OrderListViewTests(TestCase):
    """Tests for the order list view."""

    def setUp(self):
        self.admin = _make_user('admin@example.com', is_admin=True)
        self.user = _make_user('buyer@example.com')
        self.other = _make_user('other@example.com')
        self.category = Category.objects.create(
            name='Electronics', slug='electronics',
        )
        self.product = _make_product('Widget', self.category, self.admin)
        self.order = _make_order(self.user)

    def test_redirects_anonymous_user(self):
        response = self.client.get(reverse('orders:order-list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_authenticated_user_sees_own_orders(self):
        self.client.login(email='buyer@example.com', password='StrongPass123')
        response = self.client.get(reverse('orders:order-list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.order, response.context['orders'])

    def test_other_user_does_not_see_orders(self):
        self.client.login(email='other@example.com', password='StrongPass123')
        response = self.client.get(reverse('orders:order-list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.order, response.context['orders'])

    def test_orders_ordered_newest_first(self):
        order2 = _make_order(self.user, total=Decimal('5.00'))
        self.client.login(email='buyer@example.com', password='StrongPass123')
        response = self.client.get(reverse('orders:order-list'))
        orders = list(response.context['orders'])
        self.assertEqual(orders[0], order2)
        self.assertEqual(orders[1], self.order)

    def test_template_used(self):
        self.client.login(email='buyer@example.com', password='StrongPass123')
        response = self.client.get(reverse('orders:order-list'))
        self.assertTemplateUsed(response, 'orders/list.html')


class OrderDetailViewTests(TestCase):
    """Tests for the order detail view."""

    def setUp(self):
        self.admin = _make_user('admin2@example.com', is_admin=True)
        self.user = _make_user('buyer2@example.com')
        self.other = _make_user('other2@example.com')
        self.category = Category.objects.create(
            name='Gadgets', slug='gadgets',
        )
        self.product = _make_product('Gadget', self.category, self.admin)
        self.order = _make_order(self.user)
        self.item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('14.99'),
        )

    def test_redirects_anonymous_user(self):
        url = reverse('orders:order-detail', kwargs={'pk': self.order.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_owner_can_view_order_detail(self):
        self.client.login(email='buyer2@example.com', password='StrongPass123')
        url = reverse('orders:order-detail', kwargs={'pk': self.order.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['order'], self.order)

    def test_other_user_gets_404(self):
        self.client.login(email='other2@example.com', password='StrongPass123')
        url = reverse('orders:order-detail', kwargs={'pk': self.order.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_order_items_in_context(self):
        self.client.login(email='buyer2@example.com', password='StrongPass123')
        url = reverse('orders:order-detail', kwargs={'pk': self.order.pk})
        response = self.client.get(url)
        items = list(response.context['items'])
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0], self.item)

    def test_template_used(self):
        self.client.login(email='buyer2@example.com', password='StrongPass123')
        url = reverse('orders:order-detail', kwargs={'pk': self.order.pk})
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'orders/detail.html')

    def test_nonexistent_order_returns_404(self):
        self.client.login(email='buyer2@example.com', password='StrongPass123')
        url = reverse('orders:order-detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class OrderManagerTests(TestCase):
    """Tests for OrderManager.get_user_orders_with_details."""

    def setUp(self):
        self.admin = _make_user('mgr_admin@example.com', is_admin=True)
        self.user = _make_user('mgr_buyer@example.com')
        self.other = _make_user('mgr_other@example.com')
        self.category = Category.objects.create(
            name='Tools', slug='tools',
        )
        self.product = _make_product('Hammer', self.category, self.admin)
        self.order1 = _make_order(self.user, total=Decimal('10.00'))
        self.order2 = _make_order(self.user, total=Decimal('20.00'))
        _make_order(self.other, total=Decimal('5.00'))

    def test_returns_only_user_orders(self):
        qs = Order.objects.get_user_orders_with_details(self.user.pk)
        self.assertEqual(qs.count(), 2)
        for order in qs:
            self.assertEqual(order.user_id, self.user.pk)

    def test_ordered_newest_first(self):
        qs = list(Order.objects.get_user_orders_with_details(self.user.pk))
        self.assertGreaterEqual(qs[0].created_at, qs[1].created_at)

    def test_items_prefetched(self):
        OrderItem.objects.create(
            order=self.order1,
            product=self.product,
            quantity=1,
            unit_price=Decimal('10.00'),
        )
        qs = Order.objects.get_user_orders_with_details(self.user.pk)
        order = next(o for o in qs if o.pk == self.order1.pk)
        # Access prefetched items without triggering an extra query
        self.assertEqual(len(order.items.all()), 1)


class ProcessPaymentViewTests(TestCase):
    """Tests for payment processing flow."""

    def setUp(self):
        self.admin = _make_user('payment_admin@example.com', is_admin=True)
        self.user = _make_user('payment_user@example.com')
        self.other = _make_user('payment_other@example.com')
        self.category = Category.objects.create(
            name='Accessories',
            slug='accessories',
        )
        self.product = _make_product('Cable', self.category, self.admin)
        self.order = _make_order(self.user, status=STATUS_PENDING)
        self.url = reverse(
            'process-payment',
            kwargs={'order_id': self.order.pk},
        )

    def test_redirects_anonymous_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_user_cannot_pay_another_user_order(self):
        self.client.login(
            email='payment_other@example.com',
            password='StrongPass123',
        )
        response = self.client.post(
            self.url,
            data={'stripe_token': 'tok_visa'},
        )
        self.assertEqual(response.status_code, 404)

    @patch('orders.views.StripePaymentProvider.process_payment')
    def test_successful_payment_sets_order_paid_and_creates_payment(
        self,
        mock_process_payment,
    ):
        mock_process_payment.return_value = PaymentResult(
            success=True,
            transaction_id='ch_test_123',
        )
        self.client.login(
            email='payment_user@example.com',
            password='StrongPass123',
        )

        response = self.client.post(
            self.url,
            data={'stripe_token': 'tok_visa'},
        )

        self.assertRedirects(
            response,
            reverse('orders:order-detail', kwargs={'pk': self.order.pk}),
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, STATUS_PAID)

        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.status, PAYMENT_STATUS_SUCCEEDED)
        self.assertEqual(payment.transaction_id, 'ch_test_123')
        self.assertEqual(payment.amount, self.order.total_amount)

    @patch('orders.views.StripePaymentProvider.process_payment')
    def test_failed_payment_keeps_order_pending_and_stores_failed_payment(
        self,
        mock_process_payment,
    ):
        mock_process_payment.return_value = PaymentResult(
            success=False,
            error_message='Payment rejected.',
        )
        self.client.login(
            email='payment_user@example.com',
            password='StrongPass123',
        )

        response = self.client.post(
            self.url,
            data={'stripe_token': 'tok_chargeDeclined'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, STATUS_PENDING)

        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.status, PAYMENT_STATUS_FAILED)
        self.assertEqual(payment.transaction_id, '')
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('Payment rejected.', messages)
