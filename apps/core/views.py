"""Views for the public landing page and signed-in dashboard shell."""

import requests
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

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


def signout(request):
    """Log the user out and return them to the public landing page."""
    if request.method == 'POST':
        logout(request)
        return redirect('landing')

    return redirect('home')