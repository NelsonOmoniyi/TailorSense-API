from django.urls import path
from . import views

urlpatterns = [
    # file path for user auth page
    path('', views.auth, name='user'),
]
