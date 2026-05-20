from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from pages.models import Category


class HomePageCategoryLinksTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_home_page_renders_category_as_clickable_link(self):
        category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            description='Devices and gadgets',
            is_active=True,
        )

        response = self.client.get(reverse('pages:home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse(
                'store:product-list-by-category',
                kwargs={'slug': category.slug},
            ),
        )
