from django import forms
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from store.models import Product
from pages.models import Category


class ProductForm(forms.ModelForm):
    """Form for creating and editing products in the admin panel."""

    class Meta:
        model = Product
        fields = [
            'name',
            'slug',
            'description',
            'brand',
            'price',
            'stock',
            'image',
            'is_available',
            'category',
        ]
        labels = {
            'name': _('Name'),
            'slug': _('Slug'),
            'description': _('Description'),
            'brand': _('Brand'),
            'price': _('Price'),
            'stock': _('Stock'),
            'image': _('Image URL'),
            'is_available': _('Available'),
            'category': _('Category'),
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'slug': forms.TextInput(
                attrs={'placeholder': _('Auto-generated from name if empty')}
            ),
            'image': forms.URLInput(
                attrs={'placeholder': 'https://example.com/image.jpg'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(
            is_active=True,
        )
        self.fields['slug'].required = False

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        name = self.cleaned_data.get('name', '')
        if not slug and name:
            slug = slugify(name)
        return slug
