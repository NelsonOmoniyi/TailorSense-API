"""HTTP views for public pages and the authenticated TailorSense interface.

Core owns browser-facing HTML, form handling, navigation, and user feedback.
Domain APIs remain the source of truth for account and fabric operations; the
views here translate between browser requests and those API contracts. This
keeps templates presentation-focused and prevents the UI from duplicating API
validation or persistence rules.
"""

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps import users
from apps.users.auth import authenticated_required, get_authenticated_user
from apps.users.models import UserProfile


def landing(request):
    """Render the public entry page without loading authenticated workspace data."""
    return render(request, 'landing.html')


def _api_error_message(response, fallback):
    """Turn DRF's field/detail error payload into a message suitable for HTML.

    API clients receive structured JSON errors. Browser forms instead display a
    concise message near the form, so this adapter preserves useful validation
    details while tolerating non-JSON responses from unavailable services.
    """
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
    """Forward the browser CSRF token when core makes a session-authenticated API call.

    The API request is issued server-side, but it represents a browser form
    submission. Passing the submitted browser token lets DRF apply the same
    CSRF protection it uses for direct session-authenticated requests.
    """
    csrf_token = request.COOKIES.get(settings.CSRF_COOKIE_NAME)
    return {'X-CSRFToken': csrf_token} if csrf_token else {}


def _copy_api_cookies(api_response, response):
    """Relay authentication cookies from the login API to the user's browser.

    The API establishes the Django session; without copying its Set-Cookie
    values onto core's redirect, the browser would not be authenticated on the
    next page. Cookie security attributes come from Django settings so this
    proxy does not weaken the project's session or CSRF policy.
    """
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
    """Render registration UI and delegate account creation to the user API.

    Core deliberately does not create users itself. The API owns field and
    password validation plus persistence; core only forwards submitted form
    data and converts the API result into a redirect or an inline form error.
    """
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
    """Render sign-in UI and establish the browser session through the user API.

    On success, the API's session cookie must be relayed before redirecting to
    Home. Invalid credentials and temporary API failures stay on the sign-in
    page so users can retry without losing their form context.
    """
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

    The browser's session cookie is forwarded to the fabric API, which remains
    responsible for authentication and catalog data. Returning an explicit
    error separately from the records is important: an API outage must not look
    like a valid but empty catalog in Home or Fabrics.
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


def _fetch_measurement_api(request, endpoint):
    """Fetch one authenticated Measurements API resource for a core page.

    The user's session cookie is forwarded to the API, which scopes profile
    records to the authenticated account. API failures are returned separately
    from data so an outage is never presented as an empty measurement history.
    """
    if get_authenticated_user(request) is None:
        return {'error': 'Your session is no longer valid. Please sign in again.'}, None

    api_url = request.build_absolute_uri(endpoint)
    try:
        response = requests.get(api_url, cookies=request.COOKIES, timeout=10)
        if response.status_code == 200:
            return None, response.json()
        if response.status_code == 401:
            return {'error': 'Your session is no longer valid. Please sign in again.'}, None
        return {'error': 'The measurements service is temporarily unavailable. Please try again shortly.'}, None
    except requests.RequestException:
        return {'error': 'We could not load measurements at this time. Please try again shortly.'}, None


@authenticated_required
def home(request):
    """Build the Home overview from the authenticated fabric API response.

    The count and preview use the same response that powers the catalog. Other
    dashboard counts remain zero until their corresponding domain models and
    APIs exist, rather than implying that sample records are persisted.
    """
    error, fabrics = _fetch_fabrics_from_api(request)
    error, measurements = _fetch_measurement_api(request, '/api/measurements/profiles/')

    data = {
        'fabrics_count': len(fabrics or []),
        'measurements_count': len(measurements or []),
        'error': error,
    }
    
    return render(request, 'home.html', { 'data': data })


@authenticated_required
def home_section(request, section):
    """Render account, history, or settings content embedded in Home.

    These sections currently share ``home.html`` because they are small
    account-level views rather than separate data-owning applications. The
    ``section`` key selects one conditional block; Measurements, Fabrics,
    Styles, and Recommendations are routed to their own dashboard templates
    below instead of being mixed into Home.
    """
    pages = {
        'profile': ('My Profile', 'Your account details and style preferences.'),
        'orders': ('Orders / History', 'Your tailoring and style activity.'),
        'settings': ('Settings', 'Your application preferences.'),
    }
    title, description = pages[section]

    # The profile page hosts the Add-Bio modal, which posts here as ``desc``.
    if section == 'profile' and request.method == 'POST':
        bio_value = request.POST.get('desc', '').strip()[:350]
        UserProfile.objects.update_or_create(
            user=request.user,
            defaults={'bio': bio_value},
        )
        messages.success(request, 'Your bio has been saved.')
        return redirect('profile')

    try:
        # Older accounts may not have a profile row, so profile display must remain optional.
        phone = request.user.profile.phone
        bio = request.user.profile.bio
    except ObjectDoesNotExist:
        phone = ''
        bio = ''

    return render(request, 'home.html', {
        'section': section,
        'page_title': title,
        'page_description': description,
        'profile_phone': phone,
        'profile_bio': bio,
    })


@authenticated_required
def measurements_dashboard(request):
    """Render the signed-in user's saved measurement profiles and type catalog."""
    types_error, measurement_types = _fetch_measurement_api(request, '/api/measurements/types/')
    profiles_error, profiles = _fetch_measurement_api(request, '/api/measurements/profiles/')
    return render(request, 'measurements/dashboard.html', {
        'measurement_types': measurement_types or [],
        'profiles': profiles or [],
        'error': types_error or profiles_error,
    })


@authenticated_required
@require_POST
def add_measurement_profile(request):
    """Relay one profile and its nonblank measurement values to the API.

    HTML submits parallel repeated fields for type codes and values. Core pairs
    those fields, omits untouched inputs, and lets the API validate stable
    codes, enforce ownership, and persist the profile and its rows atomically.
    """
    type_codes = request.POST.getlist('measurement_type_code')
    values = request.POST.getlist('measurement_value')
    measurement_entries = [
        {'measurement_type': code, 'value': value}
        for code, value in zip(type_codes, values)
        if value.strip()
    ]
    payload = {
        'name': request.POST.get('name', '').strip(),
        'gender': request.POST.get('gender', '').strip(),
        'unit': request.POST.get('unit', 'cm'),
        'measurements': measurement_entries,
    }

    try:
        response = requests.post(
            request.build_absolute_uri('/api/measurements/profiles/'),
            json=payload,
            cookies=request.COOKIES,
            headers=_api_headers(request),
            timeout=10,
        )
    except requests.RequestException:
        messages.error(request, 'We could not save this measurement profile. Please try again shortly.')
        return redirect('measurements')

    if response.status_code == 201:
        messages.success(request, 'Measurement profile saved.')
    elif response.status_code == 401:
        messages.error(request, 'Your session is no longer valid. Please sign in again.')
        return redirect('login')
    elif response.status_code == 400:
        messages.error(request, _api_error_message(response, 'Please review the measurement details.'))
    else:
        messages.error(request, 'The measurements service is temporarily unavailable. Please try again shortly.')

    return redirect('measurements')


@authenticated_required
def styles_dashboard(request):
    """Render Styles UI from its own template under the shared base shell.

    Style records and filters will be supplied by the Styles domain when it is
    implemented; this view intentionally does not manufacture catalog data.
    """
    return render(request, 'styles/dashboard.html')


@authenticated_required
def recommendations_dashboard(request):
    """Render Recommendations UI from its own template under the shared base shell.

    The future recommendation service can populate this page without moving
    presentation back into Home or changing the shared navigation contract.
    """
    return render(request, 'recommendations/dashboard.html')


@authenticated_required
def fabric_dashboard(request):
    """Render the Fabrics app dashboard using API-owned catalog records.

    Search is applied to the returned representation in core because the
    current catalog API exposes a complete authenticated list. If filtering
    later moves into the API, this view can pass the query through without
    changing the template's ownership or the shared base shell.
    """
    error, fabrics = _fetch_fabrics_from_api(request)
    query = request.GET.get('q', '').strip()
    if fabrics and query:
        normalized_query = query.casefold()
        searchable_fields = ('fabric_name', 'fiber_category', 'fiber', 'fabric_type', 'composition')
        fabrics = [
            fabric for fabric in fabrics
            if any(normalized_query in str(fabric.get(field, '')).casefold() for field in searchable_fields)
        ]
    return render(request, 'fabrics/dashboard.html', {
        'fabrics': fabrics,
        'error': error,
        'query': query,
    })


@authenticated_required
@require_POST
def add_fabric(request):
    """Relay the catalog form to the fabric API and translate its result for HTML.

    The API is the only layer that validates and persists a Fabric. This view
    forwards the session and CSRF token, then uses Django messages plus a
    redirect so a browser refresh cannot submit the same form twice.
    """
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

    # API success and validation/authentication failures each map to a clear
    # browser outcome; unexpected statuses use the common service-unavailable message.
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
    """Ask the user API to sign out, then always clear this browser's local session.

    The POST-only browser action shares the user API's logout path. Local logout
    still runs if that HTTP request fails, so a transient API outage cannot
    leave the current browser signed in. A GET is treated as navigation back to
    Home rather than as a state-changing operation.
    """
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
