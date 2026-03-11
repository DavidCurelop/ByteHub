from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom manager for User model."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

    def get_all_admins(self):
        return self.filter(is_admin=True)

    def get_active_clients_with_orders(self):
        # Will be refined with order filtering once the Order model is available.
        return self.filter(is_active=True, is_admin=False)


class User(AbstractBaseUser):
    """Custom user model using email as the unique identifier."""

    email = models.EmailField(_('email'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    phone = models.CharField(_('phone'), max_length=20, blank=True)
    is_admin = models.BooleanField(_('admin status'), default=False)
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('date joined'), auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    def has_admin_privileges(self):
        return self.is_admin

    def get_client_lifetime_value(self):
        from decimal import Decimal
        return Decimal('0.00')

    # Required by Django admin
    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

    @property
    def is_staff(self):
        return self.is_admin

    def clean(self):
        from django.core.exceptions import ValidationError
        self.email = self.__class__.objects.normalize_email(self.email)
