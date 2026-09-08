from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

# Create your views here.
#Public page for visitors
def landing(request):
    return render(request, 'landing.html')

#Private page for logged-in users
@login_required
def home(request):
    return render(request, 'home.html')


def signout(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')

    return redirect('home')