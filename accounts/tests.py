from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext as _

User = get_user_model()


class UserRegistrationTest(TestCase):
    """Tests for HU-01: User Registration."""

    def test_successful_registration(self):
        response = self.client.post(reverse('accounts:register'), {
            'email': 'newuser@example.com',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'phone': '555-1234',
            'password': 'StrongPass123',
            'password_confirm': 'StrongPass123',
        })
        self.assertRedirects(response, reverse('accounts:login'))
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_registration_duplicate_email(self):
        User.objects.create_user(
            email='existing@example.com',
            password='pass',
            first_name='A',
            last_name='B',
        )
        response = self.client.post(reverse('accounts:register'), {
            'email': 'existing@example.com',
            'first_name': 'C',
            'last_name': 'D',
            'password': 'StrongPass123',
            'password_confirm': 'StrongPass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['form'],
            'email',
            _('A user with this email already exists.'),
        )

    def test_registration_password_mismatch(self):
        response = self.client.post(reverse('accounts:register'), {
            'email': 'mismatch@example.com',
            'first_name': 'X',
            'last_name': 'Y',
            'password': 'StrongPass123',
            'password_confirm': 'Different999',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            User.objects.filter(email='mismatch@example.com').exists()
        )


class UserLoginTest(TestCase):
    """Tests for HU-02: User Login."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='CorrectPass1',
            first_name='Test',
            last_name='User',
        )

    def test_login_correct_credentials(self):
        response = self.client.post(reverse('accounts:login'), {
            'email': 'test@example.com',
            'password': 'CorrectPass1',
        })
        self.assertRedirects(response, reverse('accounts:profile'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_wrong_password(self):
        response = self.client.post(reverse('accounts:login'), {
            'email': 'test@example.com',
            'password': 'WrongPass99',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_unknown_email(self):
        response = self.client.post(reverse('accounts:login'), {
            'email': 'nobody@example.com',
            'password': 'AnyPass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class UserLogoutTest(TestCase):
    """Tests for HU-03: User Logout."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='logout@example.com',
            password='LogoutPass1',
            first_name='Log',
            last_name='Out',
        )
        self.client.force_login(self.user)

    def test_logout_via_post(self):
        response = self.client.post(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('pages:home'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class UserProfileTest(TestCase):
    """Tests for HU-04: User Profile."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='profile@example.com',
            password='ProfilePass1',
            first_name='Pro',
            last_name='File',
        )

    def test_profile_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'profile@example.com')

    def test_profile_unauthenticated_redirects(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:profile')}",
        )
