from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Review


RATING_CHOICES = [
    (1, _('1 - Poor')),
    (2, _('2 - Fair')),
    (3, _('3 - Good')),
    (4, _('4 - Very good')),
    (5, _('5 - Excellent')),
]


class ReviewForm(forms.ModelForm):
    """Form for customers to submit a product review."""

    rating = forms.TypedChoiceField(
        label=_('Rating'),
        choices=RATING_CHOICES,
        coerce=int,
        empty_value=None,
        error_messages={
            'required': _('Please select a rating.'),
            'invalid_choice': _('Rating must be between 1 and 5.'),
        },
    )
    title = forms.CharField(
        label=_('Title'),
        max_length=120,
        required=False,
        error_messages={
            'max_length': _('Title is too long.'),
        },
    )
    body = forms.CharField(
        label=_('Review'),
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
    )

    class Meta:
        model = Review
        fields = ['rating', 'title', 'body']
