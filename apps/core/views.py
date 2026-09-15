from django.contrib.auth import login as auth_login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.users.serializers import LoginSerializer, RegisterSerializer
from apps.users.services import authenticate_user, create_user

# Create your views here.
#Public page for visitors
def landing(request):
    return render(request, 'landing.html')


def login(request):
    if request.user.is_authenticated:
        return redirect('home')

    error = None
    if request.method == 'POST':
        serializer = LoginSerializer(data=request.POST)
        if serializer.is_valid():
            user = authenticate_user(request=request, **serializer.validated_data)
            if user is not None:
                auth_login(request, user)
                return redirect('home')
            error = 'Invalid email or password.'
        else:
            error = 'Enter a valid email and password.'

    return render(request, 'login.html', {'error': error})


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    error = None
    if request.method == 'POST':
        serializer = RegisterSerializer(data=request.POST)
        if serializer.is_valid():
            create_user(**serializer.validated_data)
            return redirect('login')
        error = '; '.join(
            message
            for messages in serializer.errors.values()
            for message in messages
        )

    return render(request, 'register.html', {'error': error})

#Private page for logged-in users
@login_required
def home(request):
    return render(request, 'home.html')


def signout(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')

    return redirect('home')