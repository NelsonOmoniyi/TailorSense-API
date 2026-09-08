from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# Create your views here.
#Public page for visitors
def landing(request):
    return render(request, 'landing.html')
#Private page for logged-in users
@login_required
def home(request):
    return HttpResponse("Starter Project Off To A Good Start!")