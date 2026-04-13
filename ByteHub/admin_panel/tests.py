from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from pages.models import Category
from store.models import Product

User = get_user_model()


def _make_admin(email='admin@test.com'):
    return User.objects.create_user(
        email=email,
        password='StrongPass123',
        first_name='Admin',
        last_name='User',
        is_admin=True,
    )


def _make_client(email='client@test.com'):
    return User.objects.create_user(
        email=email,
        password='StrongPass123',
        first_name='Client',
        last_name='User',
    )


def _make_category(name='Tech', slug='tech'):
    return Category.objects.create(name=name, slug=slug)


def _make_product(name, category, admin, is_available=True):
    return Product.objects.create(
        name=name,
        slug=name.lower().replace(' ', '-'),
        price='99.99',
        stock=10,
        is_available=is_available,
        category=category,
        created_by=admin,
    )


class AdminRequiredDecoratorTests(TestCase):
    """Test the admin_required decorator for all admin views."""

    def setUp(self):
        self.admin = _make_admin()
        self.client_user = _make_client()
        self.category = _make_category()
        self.product = _make_product(
            'Test Product', self.category, self.admin,
        )
        self.list_url = reverse('admin_panel:product-list')
        self.create_url = reverse('admin_panel:product-create')
        self.edit_url = reverse(
            'admin_panel:product-edit', kwargs={'pk': self.product.pk}
        )
        self.deactivate_url = reverse(
            'admin_panel:product-deactivate', kwargs={'pk': self.product.pk}
        )

    def test_anonymous_user_redirected_to_login(self):
        for url in [self.list_url, self.create_url, self.edit_url]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn('/accounts/login/', response['Location'])

    def test_non_admin_user_redirected_to_home(self):
        self.client.force_login(self.client_user)
        for url in [self.list_url, self.create_url, self.edit_url]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(
                    response,
                    reverse('pages:home'),
                    fetch_redirect_response=False,
                )

    def test_admin_user_can_access_product_list(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

    def test_deactivate_requires_post_for_anonymous(self):
        response = self.client.post(self.deactivate_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])


class AdminProductListTests(TestCase):
    """Tests for the admin product list view."""

    def setUp(self):
        self.admin = _make_admin()
        self.category = _make_category()
        self.available = _make_product(
            'Available Widget', self.category, self.admin, is_available=True,
        )
        self.unavailable = _make_product(
            'Unavailable Widget',
            self.category,
            self.admin,
            is_available=False,
        )
        self.client.force_login(self.admin)
        self.url = reverse('admin_panel:product-list')

    def test_list_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_list_shows_all_products(self):
        """Admin list shows both available and unavailable products."""
        response = self.client.get(self.url)
        self.assertContains(response, self.available.name)
        self.assertContains(response, self.unavailable.name)

    def test_list_uses_admin_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'admin_panel/products/list.html')
        self.assertTemplateUsed(response, 'admin_panel/base.html')


class AdminProductCreateTests(TestCase):
    """Tests for the admin product create view."""

    def setUp(self):
        self.admin = _make_admin()
        self.category = _make_category()
        self.client.force_login(self.admin)
        self.url = reverse('admin_panel:product-create')

    def test_get_create_form_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_panel/products/form.html')

    def test_create_product_success(self):
        data = {
            'name': 'New Gadget',
            'slug': 'new-gadget',
            'description': 'A great gadget.',
            'brand': 'ByteBrand',
            'price': '49.99',
            'stock': 5,
            'image': 'https://example.com/img.jpg',
            'is_available': True,
            'category': self.category.pk,
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(
            response,
            reverse('admin_panel:product-list'),
            fetch_redirect_response=False,
        )
        self.assertTrue(Product.objects.filter(name='New Gadget').exists())

    def test_create_product_sets_created_by(self):
        data = {
            'name': 'Another Gadget',
            'slug': 'another-gadget',
            'price': '19.99',
            'stock': 1,
            'category': self.category.pk,
        }
        self.client.post(self.url, data)
        product = Product.objects.get(name='Another Gadget')
        self.assertEqual(product.created_by, self.admin)

    def test_create_product_invalid_price_shows_errors(self):
        data = {
            'name': 'Bad Product',
            'slug': 'bad-product',
            'price': '-5.00',
            'stock': 1,
            'category': self.category.pk,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.filter(name='Bad Product').exists())

    def test_slug_auto_generated_from_name(self):
        data = {
            'name': 'Auto Slug Product',
            'slug': '',
            'price': '9.99',
            'stock': 2,
            'category': self.category.pk,
        }
        self.client.post(self.url, data)
        self.assertTrue(
            Product.objects.filter(slug='auto-slug-product').exists()
        )


class AdminProductEditTests(TestCase):
    """Tests for the admin product edit view."""

    def setUp(self):
        self.admin = _make_admin()
        self.category = _make_category()
        self.product = _make_product(
            'Original Name', self.category, self.admin,
        )
        self.client.force_login(self.admin)
        self.url = reverse(
            'admin_panel:product-edit', kwargs={'pk': self.product.pk}
        )

    def test_get_edit_form_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_panel/products/form.html')

    def test_edit_product_success(self):
        data = {
            'name': 'Updated Name',
            'slug': 'original-name',
            'price': '150.00',
            'stock': 20,
            'is_available': True,
            'category': self.category.pk,
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(
            response,
            reverse('admin_panel:product-list'),
            fetch_redirect_response=False,
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Updated Name')
        self.assertEqual(str(self.product.price), '150.00')

    def test_edit_returns_404_for_unknown_product(self):
        url = reverse('admin_panel:product-edit', kwargs={'pk': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class AdminProductDeactivateTests(TestCase):
    """Tests for the soft-delete (deactivate) view."""

    def setUp(self):
        self.admin = _make_admin()
        self.category = _make_category()
        self.product = _make_product(
            'Active Product', self.category, self.admin, is_available=True,
        )
        self.client.force_login(self.admin)
        self.url = reverse(
            'admin_panel:product-deactivate', kwargs={'pk': self.product.pk}
        )

    def test_deactivate_sets_is_available_false(self):
        response = self.client.post(self.url)
        self.assertRedirects(
            response,
            reverse('admin_panel:product-list'),
            fetch_redirect_response=False,
        )
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_available)

    def test_deactivate_does_not_delete_record(self):
        self.client.post(self.url)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

    def test_deactivate_get_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_deactivate_returns_404_for_unknown_product(self):
        url = reverse(
            'admin_panel:product-deactivate', kwargs={'pk': 99999}
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

