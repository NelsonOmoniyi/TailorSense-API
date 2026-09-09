"""Business operations for user registration and authentication."""

from django.contrib.auth import authenticate, get_user_model
from django.db import transaction

from .models import UserProfile


User = get_user_model()


# User creation writes to two related tables. The transaction guarantees that
# either both records are created or neither record is kept.
@transaction.atomic
def create_user(*, full_name, email, phone, password, password_confirmation):
    # Django hashes the raw password inside create_user; the plain password is
    # never stored directly in the database.
    user = User.objects.create_user(
        username=email,
        email=email,
        first_name=full_name,
        password=password,
    )
    # Profile-specific data stays outside Django's built-in authentication table.
    UserProfile.objects.create(user=user, phone=phone)
    return user


def authenticate_user(*, request, email, password):
    # Centralize credential authentication so views only translate service results
    # into HTTP responses. authenticate returns None when credentials are invalid.
    return authenticate(request, username=email, password=password)