import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.shortcuts import redirect, render


def api_request(method, path, payload=None, access_token=None):
    url = f'{settings.API_BASE_URL}{path}'
    if method == 'GET' and payload:
        url = f'{url}?{urlencode(payload)}'

    body = json.dumps(payload).encode() if payload and method != 'GET' else None
    headers = {'Content-Type': 'application/json'}
    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'

    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=5) as response:
            response_body = response.read()
            return response.status, json.loads(response_body) if response_body else {}
    except HTTPError as error:
        response_body = error.read()
        try:
            data = json.loads(response_body) if response_body else {}
        except json.JSONDecodeError:
            data = {'detail': 'The API returned an invalid response.'}
        return error.code, data
    except URLError:
        return None, {'detail': 'The user API is unavailable.'}


def api_error(data):
    if 'detail' in data:
        return data['detail']
    return '; '.join(
        str(message)
        for messages in data.values()
        for message in (messages if isinstance(messages, list) else [messages])
    )


def landing(request):
    return render(request, 'landing.html')


def login(request):
    if request.session.get('access_token'):
        return redirect('home')

    error = None
    if request.method == 'POST':
        status, data = api_request('POST', 'login/', {
            'email': request.POST.get('email', ''),
            'password': request.POST.get('password', ''),
        })
        if status == 200:
            request.session['access_token'] = data['access']
            request.session['refresh_token'] = data['refresh']
            request.session['api_user'] = data['user']
            return redirect('home')
        error = api_error(data)

    return render(request, 'login.html', {'error': error})


def register(request):
    if request.session.get('access_token'):
        return redirect('home')

    error = None
    if request.method == 'POST':
        status, data = api_request('POST', 'register/', {
            'full_name': request.POST.get('fullname', ''),
            'email': request.POST.get('email', ''),
            'phone': request.POST.get('phone', ''),
            'password': request.POST.get('password', ''),
            'password_confirmation': request.POST.get('repeat_password', ''),
        })
        if status == 201:
            return redirect('login')
        error = api_error(data)

    return render(request, 'register.html', {'error': error})


def home(request):
    access_token = request.session.get('access_token')
    user = request.session.get('api_user')
    if not access_token or not user:
        return redirect('login')

    status, data = api_request(
        'GET',
        'profile/',
        {'email': user.get('email', '')},
        access_token,
    )
    if status != 200:
        request.session.flush()
        return redirect('login')

    request.session['api_user'] = data
    return render(request, 'home.html', {'user': data})


def signout(request):
    if request.method == 'POST':
        user = request.session.get('api_user', {})
        api_request(
            'POST',
            'logout/',
            {
                'email': user.get('email', ''),
                'refresh': request.session.get('refresh_token', ''),
            },
            request.session.get('access_token'),
        )
        request.session.flush()
        return redirect('login')

    return redirect('home')
