"""Views for user-related API operations."""

from django.contrib.auth import authenticate, get_user_model, login as auth_login
from django.shortcuts import render, redirect


User = get_user_model()

# Render the account creation page.
def register(request):
    error = None

    if request.method == 'POST':
        fullname = request.POST.get('fullname', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        repeat_password = request.POST.get('repeat_password', '')

        if not all((fullname, email, phone, password, repeat_password)):
            error = 'All fields are required.'
        elif password != repeat_password:
            error = 'Passwords do not match.'
        elif User.objects.filter(username=email).exists():
            error = 'An account with this email already exists.'
        else:
            User.objects.create_user(
                username=email,
                email=email,
                first_name=fullname,
                password=password,
            )
            return redirect('login')  # Redirect to the login page after successful registration

    return render(request, 'register.html', {'error': error})


# Render the login page with its email and password fields.
def login(request):
    error = None

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect('home')

        error = 'Invalid email or password.'

    return render(request, 'login.html', {'error': error})


