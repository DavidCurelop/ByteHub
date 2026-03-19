from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetView
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _

from .forms import SafePasswordResetForm, UserLoginForm, UserRegistrationForm


class UserPasswordResetView(PasswordResetView):
    """Send reset link and always show a neutral message."""

    template_name = 'auth/password_reset.html'
    form_class = SafePasswordResetForm
    email_template_name = 'auth/password_reset_email.html'
    subject_template_name = 'auth/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _(
                'If an account exists for that email, we sent a password '
                'reset link.'
            ),
        )
        return response


class UserPasswordResetConfirmView(PasswordResetConfirmView):
    """Allow users to set a new password and redirect to login."""

    template_name = 'auth/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:login')
    post_reset_login = False
    reset_url_token = 'set-password'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('Your password has been updated. Please log in.'),
        )
        return response


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
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            )
            return redirect(next_url if safe_next else 'accounts:profile')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@require_POST
def logout_view(request):
    """Handle user logout via POST."""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, _('You have been logged out.'))
    return redirect('pages:home')


@login_required
def profile_view(request):
    """Display the authenticated user's profile."""
    return render(request, 'accounts/profile.html', {'user': request.user})
