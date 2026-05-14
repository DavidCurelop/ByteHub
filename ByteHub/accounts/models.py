import re
from decimal import Decimal

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _


PHONE_PATTERN = re.compile(r'^[0-9+()\-\s]{7,20}$')


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
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_admin') is not True:
            raise ValueError(_('Superuser must have is_admin=True.'))
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        if extra_fields.get('is_active') is not True:
            raise ValueError(_('Superuser must have is_active=True.'))

        return self.create_user(email, password, **extra_fields)

    def get_all_admins(self):
        return self.filter(is_admin=True)

    def get_active_clients(self):
        return self.filter(is_active=True, is_admin=False)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model using email as the unique identifier."""

    email = models.EmailField(_('email'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    phone = models.CharField(_('phone'), max_length=20, blank=True)
    is_admin = models.BooleanField(_('admin status'), default=False)
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('date joined'), auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        constraints = [
            UniqueConstraint(Lower('email'), name='accounts_user_email_ci_uniq'),
        ]

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    def has_admin_privileges(self):
        return self.is_admin

    def get_client_lifetime_value(self):
        return Decimal('0.00')

    def clean(self):
        from django.core.exceptions import ValidationError

        self.email = self.__class__.objects.normalize_email(self.email)
        self.first_name = (self.first_name or '').strip()
        self.last_name = (self.last_name or '').strip()
        self.phone = (self.phone or '').strip()

        errors = {}

        if self.phone and not PHONE_PATTERN.match(self.phone):
            errors['phone'] = _('Enter a valid phone number.')

        if self.is_admin and not self.is_active:
            errors['is_active'] = _('Admin users must be active.')

        if errors:
            raise ValidationError(errors)
