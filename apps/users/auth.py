"""Shared authentication helpers for the TailorSense project.

All authenticated requests should pass through this module so the same checks are
used for the web app and the API layer. This prevents duplicated login logic and
keeps the session identity rules consistent across the application.
"""

import hashlib

from django.contrib.auth import login as auth_login


def hash_session_key(session_key, email=None, phone=None):
    """Return the stored hash for the browser session identity.

    The project validates an authenticated browser session against a hash built
    from the current session key, the user's email, and the phone number when
    available. This keeps the raw session identity and account details out of the
    session store while preserving a stable identity check for auth requests.
    """
    if not session_key:
        return ''

    identity_parts = [session_key, (email or '').strip().lower(), (phone or '').strip()]
    identity_string = '|'.join(part for part in identity_parts if part)
    return hashlib.sha256(identity_string.encode('utf-8')).hexdigest()


def _user_phone(user):
    """Return the current user's phone number from the profile when available."""
    profile = getattr(user, 'profile', None)
    if profile is not None:
        phone = getattr(profile, 'phone', '')
        if phone:
            return str(phone).strip()

    phone = getattr(user, 'phone', '')
    if phone:
        return str(phone).strip()

    return ''


def login_user(request, user):
    """Persist the auth state for the current user using the session contract."""
    auth_login(request, user)
    phone = _user_phone(user)
    request.session['session_key_hash'] = hash_session_key(
        request.session.session_key,
        (user.email or '').strip().lower(),
        phone,
    )
    request.session['user_email'] = (user.email or '').strip().lower()
    request.session['user_phone'] = phone
    return user


def get_authenticated_user(request):
    """Return the current authenticated user only when the session is valid.

    This is the single authorization gate for project-level requests. It verifies
    that the Django session is still active, that the stored session hash matches
    the current session key, and that the session email and phone still match the
    authenticated user.
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return None

    session_key = request.session.session_key
    if not session_key:
        return None

    stored_hash = request.session.get('session_key_hash')
    stored_email = (request.session.get('user_email') or '').strip().lower()
    stored_phone = (request.session.get('user_phone') or '').strip()
    expected_hash = hash_session_key(
        session_key,
        (user.email or '').strip().lower(),
        _user_phone(user),
    )
    expected_email = (user.email or '').strip().lower()
    expected_phone = _user_phone(user)

    if stored_hash != expected_hash:
        return None

    if stored_email and stored_email != expected_email:
        return None

    if stored_phone and stored_phone != expected_phone:
        return None

    return user


def require_authenticated_user(request):
    """Project-wide auth gate used by the web flow and protected API endpoints."""
    return get_authenticated_user(request) is not None


def authenticated_required(view_func):
    """Decorator that protects any Django view with the project-wide session check."""

    def wrapped(request, *args, **kwargs):
        if not require_authenticated_user(request):
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden('Authentication required.')
        return view_func(request, *args, **kwargs)

    wrapped.__name__ = view_func.__name__
    wrapped.__doc__ = view_func.__doc__
    return wrapped
