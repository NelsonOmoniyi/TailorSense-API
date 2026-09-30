"""Views for the public landing page and signed-in dashboard shell."""

import requests
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.users.auth import authenticated_required, get_authenticated_user


def landing(request):
    # Public page for visitors.
    return render(request, 'landing.html')


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
@login_required
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
    """Log the user out and return them to the public landing page."""
    if request.method == 'POST':
        logout(request)
        return redirect('landing')

    return redirect('home')
