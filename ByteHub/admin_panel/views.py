from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from store.models import Product

from .decorators import admin_required
from .forms import ProductForm


@admin_required
def product_list(request):
    """List all products (available and unavailable) for the admin."""
    products = (
        Product.objects
        .select_related('category', 'created_by')
        .order_by('-created_at')
    )
    return render(
        request,
        'admin_panel/products/list.html',
        {'products': products},
    )


@admin_required
def product_create(request):
    """Create a new product."""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.save()
            messages.success(
                request,
                _('Product "%(name)s" created successfully.')
                % {'name': product.name},
            )
            return redirect('admin_panel:product-list')
    else:
        form = ProductForm()

    return render(
        request,
        'admin_panel/products/form.html',
        {
            'form': form,
            'form_title': _('Create Product'),
            'submit_label': _('Create'),
        },
    )


@admin_required
def product_edit(request, pk):
    """Edit an existing product."""
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                _('Product "%(name)s" updated successfully.')
                % {'name': product.name},
            )
            return redirect('admin_panel:product-list')
    else:
        form = ProductForm(instance=product)

    return render(
        request,
        'admin_panel/products/form.html',
        {
            'form': form,
            'form_title': _('Edit Product'),
            'submit_label': _('Save Changes'),
            'product': product,
        },
    )


@admin_required
@require_POST
def product_deactivate(request, pk):
    """Soft-delete: set is_available=False instead of deleting the record."""
    product = get_object_or_404(Product, pk=pk)
    product.is_available = False
    product.save(update_fields=['is_available'])
    messages.success(
        request,
        _('Product "%(name)s" has been deactivated.')
        % {'name': product.name},
    )
    return redirect('admin_panel:product-list')
