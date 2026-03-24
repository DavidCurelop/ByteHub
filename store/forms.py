from django import forms
from django.utils.translation import gettext_lazy as _


class CheckoutForm(forms.Form):
    """Checkout form for selecting an existing address or creating one."""

    ADDRESS_OPTION_EXISTING = 'existing'
    ADDRESS_OPTION_NEW = 'new'

    ADDRESS_OPTION_CHOICES = (
        (ADDRESS_OPTION_EXISTING, _('Use saved address')),
        (ADDRESS_OPTION_NEW, _('Add a new address')),
    )

    address_option = forms.ChoiceField(
        label=_('Shipping address option'),
        choices=ADDRESS_OPTION_CHOICES,
        initial=ADDRESS_OPTION_EXISTING,
        widget=forms.RadioSelect,
    )
    address_id = forms.IntegerField(required=False)

    street = forms.CharField(label=_('Street'), max_length=255, required=False)
    city = forms.CharField(label=_('City'), max_length=120, required=False)
    state = forms.CharField(label=_('State'), max_length=120, required=False)
    zip_code = forms.CharField(label=_('ZIP code'), max_length=20, required=False)
    country = forms.CharField(
        label=_('Country'),
        max_length=120,
        required=False,
    )
    is_default = forms.BooleanField(
        label=_('Save as default address'),
        required=False,
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        option = cleaned_data.get('address_option')

        if option == self.ADDRESS_OPTION_EXISTING:
            if not cleaned_data.get('address_id'):
                raise forms.ValidationError(
                    _('Please select a saved shipping address.'),
                )
            return cleaned_data

        if option == self.ADDRESS_OPTION_NEW:
            required_fields = ['street', 'city', 'state', 'zip_code', 'country']
            missing_fields = [
                field_name
                for field_name in required_fields
                if not cleaned_data.get(field_name)
            ]
            if missing_fields:
                raise forms.ValidationError(
                    _('Please complete all required address fields.'),
                )

        return cleaned_data
