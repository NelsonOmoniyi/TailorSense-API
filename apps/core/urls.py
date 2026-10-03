from django.urls import path
from . import views

urlpatterns = [
    # Public entry and account-form pages; their POST handlers delegate to the user API.
    path('', views.landing, name='landing'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    # Home keeps account/history/settings sections; domain dashboards render their own templates.
    path('home/', views.home, name='home'),
    path('profile/', views.home_section, {'section': 'profile'}, name='profile'),
    path('measurements/', views.measurements_dashboard, name='measurements'),
    # Fabrics has a data-backed API; core renders its dashboard and relays add-form submissions.
    path('fabrics/', views.fabric_dashboard, name='fabrics-dashboard'),
    path('fabrics/add/', views.add_fabric, name='add-fabric'),
    # Each emerging domain has its own dashboard template and shares the shell from base.html.
    path('styles/', views.styles_dashboard, name='styles'),
    path('recommendations/', views.recommendations_dashboard, name='recommendations'),
    # Account-level pages remain conditional sections in Home until they grow into their own apps.
    path('orders/', views.home_section, {'section': 'orders'}, name='orders'),
    path('settings/', views.home_section, {'section': 'settings'}, name='settings'),
    path('signout/', views.signout, name='signout'),
]


