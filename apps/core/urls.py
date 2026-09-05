from django.urls import path
from . import views

urlpatterns = [
    # file path for home page
    path('', views.home, name='home'),
]


