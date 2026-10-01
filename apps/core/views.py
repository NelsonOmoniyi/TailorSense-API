"""Views for the public landing page and signed-in dashboard shell."""

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.users.auth import authenticated_required, get_authenticated_user


def landing(request):
    # Public page for visitors.
    return render(request, 'landing.html')


def _api_error_message(response, fallback):
    try:
        payload = response.json()
    except ValueError:
        return fallback

    if not isinstance(payload, dict):
        return fallback
    if payload.get('detail'):
        return str(payload['detail'])

    errors = []
    for field, messages_for_field in payload.items():
        if not isinstance(messages_for_field, (list, tuple)):
            messages_for_field = [messages_for_field]
        errors.extend(
            f"{field.replace('_', ' ').capitalize()}: {message}"
            for message in messages_for_field
        )
    return '; '.join(errors) or fallback


def _api_headers(request):
    csrf_token = request.COOKIES.get(settings.CSRF_COOKIE_NAME)
    return {'X-CSRFToken': csrf_token} if csrf_token else {}


def _copy_api_cookies(api_response, response):
    for name, value in api_response.cookies.items():
        is_session = name == settings.SESSION_COOKIE_NAME
        response.set_cookie(
            name,
            value,
            httponly=settings.SESSION_COOKIE_HTTPONLY if is_session else settings.CSRF_COOKIE_HTTPONLY,
            secure=settings.SESSION_COOKIE_SECURE if is_session else settings.CSRF_COOKIE_SECURE,
            samesite=settings.SESSION_COOKIE_SAMESITE if is_session else settings.CSRF_COOKIE_SAMESITE,
        )


def register(request):
    error = None
    if request.method == 'POST':
        try:
            api_response = requests.post(
                request.build_absolute_uri('/api/users/register/'),
                data=request.POST,
                cookies=request.COOKIES,
                headers=_api_headers(request),
                timeout=10,
            )
        except requests.RequestException:
            error = 'Registration is temporarily unavailable. Please try again shortly.'
        else:
            if api_response.status_code == 201:
                return redirect('login')
            error = _api_error_message(api_response, 'We could not create your account.')

    return render(request, 'register.html', {'error': error})


def login(request):
    error = None
    if request.method == 'POST':
        try:
            api_response = requests.post(
                request.build_absolute_uri('/api/users/login/'),
                data=request.POST,
                cookies=request.COOKIES,
                headers=_api_headers(request),
                timeout=10,
            )
        except requests.RequestException:
            error = 'Sign in is temporarily unavailable. Please try again shortly.'
        else:
            if api_response.status_code == 200:
                response = redirect('home')
                _copy_api_cookies(api_response, response)
                return response
            error = _api_error_message(api_response, 'Invalid email or password.')

    return render(request, 'login.html', {'error': error})


def _fetch_fabrics_from_api(request):
    """Fetch the authenticated fabric list through the shared session auth gate.

    The project does not silently fall back to an empty list when the API fails;
    the caller handles the error and tells the user clearly that the catalog is
    temporarily unavailable.
    """
    user = get_authenticated_user(request)
    if user is None:
        return {'error': 'Your session is no longer valid. Please sign in again.'}, None

    api_url = request.build_absolute_uri('/api/fabrics/list/')
    try:
        response = requests.get(api_url, cookies=request.COOKIES, timeout=10)
        if response.status_code == 200:
            return None, response.json()
        if response.status_code == 401:
            return {'error': 'Your session is no longer valid. Please sign in again.'}, None
        return {'error': 'The fabric catalog is temporarily unavailable. Please try again shortly.'}, None
    except requests.RequestException:
        return {'error': 'We could not load the fabric catalog at this time. Please try again shortly.'}, None


# Private page for logged-in users.
@authenticated_required
def home(request):
    error, fabrics = _fetch_fabrics_from_api(request)
    return render(request, 'home.html', {'fabrics': fabrics, 'error': error})


@authenticated_required
def fabric_dashboard(request):
    """Render the fabric catalogue from the fabrics API response."""
    error, fabrics = _fetch_fabrics_from_api(request)
    return render(request, 'fabrics/dashboard.html', {'fabrics': fabrics, 'error': error})


@authenticated_required
@require_POST
def add_fabric(request):
    """Pass the catalogue form to the fabrics API, which owns fabric creation."""
    api_url = request.build_absolute_uri('/api/fabrics/add/')
    csrf_token = request.COOKIES.get('csrftoken')
    headers = {'X-CSRFToken': csrf_token} if csrf_token else {}

    try:
        response = requests.post(
            api_url,
            data=request.POST,
            cookies=request.COOKIES,
            headers=headers,
            timeout=10,
        )
    except requests.RequestException:
        messages.error(request, 'We could not add the fabric at this time. Please try again shortly.')
        return redirect('fabrics-dashboard')

    if response.status_code == 201:
        messages.success(request, 'Fabric added to the catalogue.')
        return redirect('fabrics-dashboard')

    if response.status_code == 401:
        messages.error(request, 'Your session is no longer valid. Please sign in again.')
        return redirect('login')

    if response.status_code == 400:
        try:
            errors = response.json()
            details = '; '.join(
                f"{field.replace('_', ' ').capitalize()}: {', '.join(values if isinstance(values, list) else [str(values)])}"
                for field, values in errors.items()
            )
        except ValueError:
            details = 'Please check the fabric details and try again.'
        messages.error(request, details)
        return redirect('fabrics-dashboard')

    messages.error(request, 'The fabric catalogue is temporarily unavailable. Please try again shortly.')
    return redirect('fabrics-dashboard')


def signout(request):
    """Call the account API, clear the browser session, and return to the landing page."""
    if request.method == 'POST':
        try:
            requests.post(
                request.build_absolute_uri('/api/users/signout/'),
                cookies=request.COOKIES,
                headers=_api_headers(request),
                timeout=10,
            )
        except requests.RequestException:
            pass
        logout(request)
        return redirect('landing')

    return redirect('home')
