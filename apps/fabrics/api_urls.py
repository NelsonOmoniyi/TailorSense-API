"""API routes for fabric inventory endpoints."""

from django.urls import path

from .api_views import fabric_list

urlpatterns = [
    # This list endpoint powers the signed-in web dashboard and any future clients.
    path('list/', fabric_list, name='fabric-api-list'),
]
