from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _

from .forms import UserLoginForm, UserRegistrationForm


def register_view(request):
    """Handle new user registration."""
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, _('Registration successful. Please log in.')
            )
            return redirect('accounts:login')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = UserLoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', '')
            safe_next = url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts=request.get_host(),
                require_https=request.is_secure(),
            )
            return redirect(next_url if safe_next else 'accounts:profile')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Handle user logout via POST."""
    if request.method == 'POST':
        logout(request)
        messages.success(request, _('You have been logged out.'))
    return redirect('pages:home')


@login_required
def profile_view(request):
    """Display the authenticated user's profile."""
    return render(request, 'accounts/profile.html', {'user': request.user})
