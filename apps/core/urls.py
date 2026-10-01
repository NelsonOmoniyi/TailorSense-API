from django.urls import path
from . import views

urlpatterns = [
    # Public page shown at the site root.
    path('', views.landing, name='landing'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    # Protected destination available after login.
    path('home/', views.home, name='home'),
    path('fabrics/', views.fabric_dashboard, name='fabrics-dashboard'),
    path('fabrics/add/', views.add_fabric, name='add-fabric'),
    path('signout/', views.signout, name='signout'),
]


