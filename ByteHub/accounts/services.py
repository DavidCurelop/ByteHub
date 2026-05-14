from django.db import transaction


@transaction.atomic
def register_user(form):
    """Persist a new user from a validated UserRegistrationForm.

    The caller is responsible for having called ``form.is_valid()`` first.
    Returns the created User instance.
    """
    return form.save()


@transaction.atomic
def update_user_profile(form):

    return form.save()
