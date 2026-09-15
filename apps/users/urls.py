from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    # Creates an account and its related UserProfile.
    path('register/', views.register, name='api-register'),
    path('login/', views.login, name='api-login'),
    path('refresh/', TokenRefreshView.as_view(), name='api-refresh'),
    path('logout/', views.logout, name='api-logout'),
    path('profile/', views.profile, name='api-profile'),
]
