from django.urls import path

from . import api_views

urlpatterns = [
    path('register/', api_views.register, name='user-api-register'),
    path('login/', api_views.login, name='user-api-login'),
    path('signout/', api_views.signout, name='user-api-signout'),
]
