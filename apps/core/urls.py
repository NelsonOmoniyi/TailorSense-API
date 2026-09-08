from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'), #default page
    path('', views.home, name='home'), #after login
]


