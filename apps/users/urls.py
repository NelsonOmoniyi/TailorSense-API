from django.urls import path
from . import views

urlpatterns = [
    # Registration is available at the users namespace root.
    path('', views.register, name='register'),
    # Login is available as a nested users route.
    path('login/', views.login, name='login'),
]
