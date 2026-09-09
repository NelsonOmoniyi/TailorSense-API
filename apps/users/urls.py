from django.urls import path
from . import views

urlpatterns = [
    # Creates an account and its related UserProfile.
    path('register/', views.register, name='api-register'),
    # Starts a Django session after valid credentials are supplied.
    path('login/', views.login, name='login'),
    # Ends the current authenticated session.
    path('logout/', views.logout, name='api-logout'),
    # Returns the account associated with the current session.
    path('me/', views.me, name='api-me'),
]
