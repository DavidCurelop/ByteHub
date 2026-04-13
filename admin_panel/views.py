import functools

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from pages.models import Category


def admin_required(view_func):
    """Decorator: only authenticated admin users may access the view."""
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_admin:
            messages.error(
                request,
                _('You do not have permission to access this page.'),
            )
            return redirect('pages:home')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def category_list(request):
    """List all categories."""
    categories = (
        Category.objects.select_related('parent', 'created_by')
        .all()
    )
    return render(
        request,
        'admin_panel/categories/list.html',
        {'categories': categories},
    )


@admin_required
def category_create(request):
    """Create a new category."""
    parents = Category.objects.select_related('parent').all()
    errors = {}

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        parent_id = request.POST.get('parent') or None

        if not name:
            errors['name'] = _('Name is required.')

        if not errors:
            parent = (
                get_object_or_404(Category, pk=parent_id)
                if parent_id else None
            )
            Category.objects.create(
                name=name,
                description=description,
                is_active=is_active,
                parent=parent,
                created_by=request.user,
            )
            messages.success(request, _('Category created successfully.'))
            return redirect('admin_panel:category-list')

        return render(
            request,
            'admin_panel/categories/form.html',
            {'errors': errors, 'parents': parents, 'post': request.POST},
        )

    return render(
        request,
        'admin_panel/categories/form.html',
        {'parents': parents},
    )


@admin_required
def category_edit(request, pk):
    """Edit an existing category."""
    category = get_object_or_404(
        Category.objects.select_related('parent', 'created_by'), pk=pk
    )
    parents = Category.objects.select_related('parent').exclude(pk=pk)
    errors = {}

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        parent_id = request.POST.get('parent') or None

        if not name:
            errors['name'] = _('Name is required.')

        if parent_id and int(parent_id) == pk:
            errors['parent'] = _(
                'A category cannot be its own parent.'
            )

        if not errors:
            category.name = name
            category.description = description
            category.is_active = is_active
            category.parent = (
                get_object_or_404(Category, pk=parent_id)
                if parent_id else None
            )
            category.save()
            messages.success(request, _('Category updated successfully.'))
            return redirect('admin_panel:category-list')

        return render(
            request,
            'admin_panel/categories/form.html',
            {
                'category': category,
                'errors': errors,
                'parents': parents,
                'post': request.POST,
            },
        )

    return render(
        request,
        'admin_panel/categories/form.html',
        {'category': category, 'parents': parents},
    )


@admin_required
def category_delete(request, pk):
    """Delete a category after verifying it has no active products."""
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        if category.products.filter(is_available=True).exists():
            messages.error(
                request,
                _('Cannot delete a category that has active products.'),
            )
            return redirect('admin_panel:category-list')
        category.delete()
        messages.success(request, _('Category deleted successfully.'))
        return redirect('admin_panel:category-list')

    return render(
        request,
        'admin_panel/categories/confirm_delete.html',
        {'category': category},
    )
