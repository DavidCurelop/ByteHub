from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from pages.models import Category

from .models import Product

User = get_user_model()


class ProductListTests(TestCase):
    """Tests for the public product listing page."""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='StrongPass123',
            first_name='Admin',
            last_name='User',
            is_admin=True,
        )
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
        )
        self.available_product = Product.objects.create(
            name='Available Product',
            slug='available-product',
            price='99.99',
            stock=10,
            is_available=True,
            category=self.category,
            created_by=self.admin_user,
        )
        self.unavailable_product = Product.objects.create(
            name='Unavailable Product',
            slug='unavailable-product',
            price='49.99',
            stock=0,
            is_available=False,
            category=self.category,
            created_by=self.admin_user,
        )

    def test_product_list_returns_200(self):
        response = self.client.get(reverse('store:product-list'))
        self.assertEqual(response.status_code, 200)

    def test_product_list_uses_correct_template(self):
        response = self.client.get(reverse('store:product-list'))
        self.assertTemplateUsed(response, 'store/product_list.html')

    def test_product_list_shows_only_available_products(self):
        response = self.client.get(reverse('store:product-list'))
        products = list(response.context['products'])
        self.assertEqual(len(products), 1)
        self.assertIn(self.available_product, products)
        self.assertNotIn(self.unavailable_product, products)

    def test_product_list_category_is_select_related(self):
        response = self.client.get(reverse('store:product-list'))
        products = list(response.context['products'])

        # Assert that accessing the related category does not trigger
        # additional queries, meaning the relation is select_related.
        with self.assertNumQueries(0):
            for product in products:
                _ = product.category.name
