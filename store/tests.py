from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from pages.models import Category

from .models import Product, Review

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


class ProductDetailTests(TestCase):
    """Tests for public product detail page."""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin2@example.com',
            password='StrongPass123',
            first_name='Admin',
            last_name='User',
            is_admin=True,
        )
        self.customer = User.objects.create_user(
            email='customer@example.com',
            password='StrongPass123',
            first_name='Customer',
            last_name='One',
        )
        self.customer_two = User.objects.create_user(
            email='customer2@example.com',
            password='StrongPass123',
            first_name='Customer',
            last_name='Two',
        )
        self.category = Category.objects.create(
            name='Audio',
            slug='audio',
        )
        self.product = Product.objects.create(
            name='Studio Headphones',
            slug='studio-headphones',
            description='Closed-back reference headphones.',
            brand='ByteSound',
            price='199.99',
            stock=7,
            is_available=True,
            image='https://example.com/headphones.jpg',
            category=self.category,
            created_by=self.admin_user,
        )
        Review.objects.create(
            product=self.product,
            user=self.customer,
            rating=5,
            title='Excellent',
            body='Great sound quality.',
            is_verified_purchase=True,
        )
        Review.objects.create(
            product=self.product,
            user=self.customer_two,
            rating=1,
            title='Bad',
            body='Not for me.',
            is_verified_purchase=False,
        )

    def test_product_detail_returns_200(self):
        response = self.client.get(
            reverse('store:product-detail', kwargs={'slug': self.product.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_product_detail_uses_slug_url(self):
        url = reverse('store:product-detail', kwargs={'slug': self.product.slug})
        self.assertEqual(url, f'/products/{self.product.slug}/')

    def test_product_detail_returns_404_for_missing_product(self):
        response = self.client.get(
            reverse('store:product-detail', kwargs={'slug': 'missing-product'})
        )
        self.assertEqual(response.status_code, 404)

    def test_product_detail_context_contains_required_fields(self):
        response = self.client.get(
            reverse('store:product-detail', kwargs={'slug': self.product.slug})
        )
        product = response.context['product']
        self.assertEqual(product.description, 'Closed-back reference headphones.')
        self.assertEqual(product.price, Decimal('199.99'))
        self.assertEqual(product.stock, 7)
        self.assertEqual(product.brand, 'ByteSound')
        self.assertEqual(product.category.name, 'Audio')
        self.assertEqual(product.image, 'https://example.com/headphones.jpg')

    def test_product_detail_shows_only_verified_reviews(self):
        response = self.client.get(
            reverse('store:product-detail', kwargs={'slug': self.product.slug})
        )
        verified_reviews = response.context['verified_reviews']
        self.assertEqual(len(verified_reviews), 1)
        self.assertEqual(verified_reviews[0].title, 'Excellent')

    def test_product_avg_rating_uses_verified_reviews_only(self):
        response = self.client.get(
            reverse('store:product-detail', kwargs={'slug': self.product.slug})
        )
        self.assertEqual(response.context['average_rating'], 5.0)
        self.assertIsInstance(response.context['average_rating'], float)

    def test_product_avg_rating_returns_float_when_no_reviews(self):
        product = Product.objects.create(
            name='Empty Product',
            slug='empty-product',
            price='9.99',
            stock=1,
            is_available=True,
            category=self.category,
            created_by=self.admin_user,
        )
        self.assertIsInstance(product.avg_rating(), float)
        self.assertEqual(product.avg_rating(), 0.0)

    def test_product_detail_average_rating_is_zero_with_no_verified_reviews(
        self,
    ):
        product = Product.objects.create(
            name='Unreviewed Product',
            slug='unreviewed-product',
            price='29.99',
            stock=3,
            is_available=True,
            category=self.category,
            created_by=self.admin_user,
        )
        response = self.client.get(
            reverse(
                'store:product-detail', kwargs={'slug': product.slug}
            )
        )
        self.assertEqual(response.context['average_rating'], 0.0)
        self.assertIsInstance(response.context['average_rating'], float)

    def test_product_detail_no_extra_queries_on_related_access(self):
        """get_public_detail() prefetches category and review users; accessing
        them after the view resolves must not trigger additional DB queries."""
        response = self.client.get(
            reverse(
                'store:product-detail', kwargs={'slug': self.product.slug}
            )
        )
        product = response.context['product']
        verified_reviews = response.context['verified_reviews']

        with self.assertNumQueries(0):
            _ = product.category.name
            for review in verified_reviews:
                _ = review.user.get_full_name()
