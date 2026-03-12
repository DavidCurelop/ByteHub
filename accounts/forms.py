from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

from .models import User


class UserRegistrationForm(forms.ModelForm):
    """Form for new user registration."""

    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    password_confirm = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone']
        labels = {
            'email': _('Email'),
            'first_name': _('First Name'),
            'last_name': _('Last Name'),
            'phone': _('Phone'),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        email = User.objects.normalize_email(email)
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                _('A user with this email already exists.')
            )
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError(_('Passwords do not match.'))
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    """Form for user authentication."""

    email = forms.EmailField(label=_('Email'))
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self._user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        if email and password:
            self._user = authenticate(
                self.request, username=email, password=password
            )
            if self._user is None:
                raise forms.ValidationError(_('Invalid email or password.'))
        return cleaned_data

    def get_user(self):
        return self._user
