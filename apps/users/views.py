"""Views for the web-based user registration and login flow."""

from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import redirect, render

from .auth import login_user


User = get_user_model()


def register(request):
    """Render the sign-up page and create a new user when the form is submitted."""
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
            # Create the standard Django user and let the view redirect to login.
            User.objects.create_user(
                username=email,
                email=email,
                first_name=fullname,
                password=password,
            )
            return redirect('login')  # Redirect to the login page after successful registration

    return render(request, 'register.html', {'error': error})


def login(request):
    """Authenticate the user and send them to the signed-in dashboard on success."""
    error = None

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login_user(request, user)
            return redirect('home')

        error = 'Invalid email or password.'

    return render(request, 'login.html', {'error': error})


