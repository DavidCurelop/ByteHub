from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from pages.models import Category
from store.models import Product

User = get_user_model()


def _make_admin(email='admin@example.com'):
    return User.objects.create_user(
        email=email,
        password='StrongPass123',
        first_name='Admin',
        last_name='User',
        is_admin=True,
    )


def _make_customer(email='customer@example.com'):
    return User.objects.create_user(
        email=email,
        password='StrongPass123',
        first_name='Customer',
        last_name='User',
    )


def _make_category(name='Electronics'):
    return Category.objects.create(name=name, slug=name.lower())


class CategoryListViewTests(TestCase):
    """Tests for the admin category list view."""

    def setUp(self):
        self.admin = _make_admin()
        self.customer = _make_customer()
        self.url = reverse('admin_panel:category-list')

    def test_admin_can_access_list(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response, f'/accounts/login/?next={self.url}'
        )

    def test_non_admin_redirected_to_home(self):
        self.client.force_login(self.customer)
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('pages:home'))

    def test_categories_appear_in_list(self):
        _make_category('Laptops')
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertContains(response, 'Laptops')


class CategoryCreateViewTests(TestCase):
    """Tests for the admin category create view."""

    def setUp(self):
        self.admin = _make_admin()
        self.url = reverse('admin_panel:category-create')

    def test_get_returns_200_for_admin(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_creates_category_and_redirects(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            self.url,
            {'name': 'New Category', 'description': '', 'is_active': 'on'},
        )
        self.assertRedirects(
            response, reverse('admin_panel:category-list')
        )
        self.assertTrue(Category.objects.filter(name='New Category').exists())

    def test_slug_auto_generated(self):
        self.client.force_login(self.admin)
        self.client.post(
            self.url,
            {'name': 'My New Category', 'is_active': 'on'},
        )
        category = Category.objects.get(name='My New Category')
        self.assertEqual(category.slug, 'my-new-category')

    def test_missing_name_shows_error(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url, {'name': '', 'is_active': 'on'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Category.objects.exists())

    def test_subcategory_creation(self):
        parent = _make_category('Parent')
        self.client.force_login(self.admin)
        self.client.post(
            self.url,
            {'name': 'Child', 'parent': parent.pk, 'is_active': 'on'},
        )
        child = Category.objects.get(name='Child')
        self.assertEqual(child.parent, parent)


class CategoryEditViewTests(TestCase):
    """Tests for the admin category edit view."""

    def setUp(self):
        self.admin = _make_admin()
        self.category = _make_category('Original')
        self.url = reverse('admin_panel:category-edit', args=[self.category.pk])

    def test_get_returns_200_for_admin(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_updates_category(self):
        self.client.force_login(self.admin)
        self.client.post(
            self.url,
            {'name': 'Updated', 'description': '', 'is_active': 'on'},
        )
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Updated')

    def test_cannot_set_self_as_parent(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            self.url,
            {
                'name': self.category.name,
                'parent': self.category.pk,
                'is_active': 'on',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.category.refresh_from_db()
        self.assertIsNone(self.category.parent)


class CategoryDeleteViewTests(TestCase):
    """Tests for the admin category delete view."""

    def setUp(self):
        self.admin = _make_admin()
        self.category = _make_category('To Delete')
        self.url = reverse(
            'admin_panel:category-delete', args=[self.category.pk]
        )

    def test_get_shows_confirm_page(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_deletes_category(self):
        self.client.force_login(self.admin)
        self.client.post(self.url)
        self.assertFalse(
            Category.objects.filter(pk=self.category.pk).exists()
        )

    def test_cannot_delete_category_with_active_products(self):
        product = Product.objects.create(
            name='Active Product',
            slug='active-product',
            price='9.99',
            stock=5,
            is_available=True,
            category=self.category,
            created_by=self.admin,
        )
        self.client.force_login(self.admin)
        response = self.client.post(self.url, follow=True)
        self.assertRedirects(
            response, reverse('admin_panel:category-list')
        )
        self.assertTrue(
            Category.objects.filter(pk=self.category.pk).exists()
        )
        product.delete()

