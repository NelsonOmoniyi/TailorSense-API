from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    # Creates an account and its related UserProfile.
    path('register/', views.register, name='api-register'),
    # Returns the same JWT credentials to web and mobile clients.
    path('login/', views.login, name='api-login'),
    # Exchanges a valid refresh JWT for a new access JWT.
    path('refresh/', TokenRefreshView.as_view(), name='api-refresh'),
    # Revokes the refresh JWT and signs out the authenticated client.
    path('logout/', views.logout, name='api-logout'),
    # Returns the account associated with the access JWT.
    path('profile/', views.profile, name='api-profile'),
]
