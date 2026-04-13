from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(_('name'), max_length=100, unique=True)
    slug = models.SlugField(_('slug'), max_length=120, unique=True)
    description = models.TextField(_('description'), blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name=_('parent category'),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_categories',
        verbose_name=_('created by'),
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self):
        return self.name

    def clean(self):
        self.name = (self.name or '').strip()
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError(
                {'parent': _('A category cannot be its own parent.')}
            )

    def save(self, *args, **kwargs):
        base_slug = slugify(self.name) or 'category'
        slug = base_slug
        counter = 1
        while True:
            qs = Category.objects.filter(slug=slug)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if not qs.exists():
                break
            slug = f'{base_slug}-{counter}'
            counter += 1
        self.slug = slug
        super().save(*args, **kwargs)
