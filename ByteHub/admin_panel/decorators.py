from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _


def admin_required(view_func):
    """Restrict access to users with is_admin=True.

    Unauthenticated users are redirected to the login page.
    Authenticated non-admin users receive a permission-denied
    message and are redirected to the home page.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_admin:
            messages.error(
                request,
                _('You do not have permission to access the admin panel.'),
            )
            return redirect('pages:home')
        return view_func(request, *args, **kwargs)

    return wrapper
