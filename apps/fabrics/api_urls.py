"""API routes for fabric inventory endpoints."""

from django.urls import path

from .api_views import fabric_list
from .api_views import add_fabric

urlpatterns = [
    # This list endpoint powers the signed-in web dashboard and any future clients.
    path('list/', fabric_list, name='fabric-api-list'),
    path('add/', add_fabric, name='fabric-api-add'),
]
