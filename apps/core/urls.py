from django.urls import path
from . import views

urlpatterns = [
    # Public page shown at the site root.
    path('', views.landing, name='landing'),
    # Server-rendered authentication pages use the same validation as the API.
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    # Protected destination available after login.
    path('home/', views.home, name='home'),
    # End the current session and return to login.
    path('signout/', views.signout, name='signout'),
]


