"""Server-rendered dashboard that consumes the authenticated fabrics API."""

import requests
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.users.auth import authenticated_required


def _fetch_fabrics_from_api(request):
    """Retrieve the current fabric inventory and return a professional error state if the API fails."""
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


@authenticated_required
@login_required
def dashboard(request):
    """Render the authenticated fabric dashboard from the API response."""
    error, fabrics = _fetch_fabrics_from_api(request)
    return render(request, 'fabrics/dashboard.html', {'fabrics': fabrics, 'error': error})
