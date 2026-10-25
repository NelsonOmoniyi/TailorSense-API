"""API routes for fabric inventory endpoints."""

from django.urls import path

from .api_views import add_fabric, fabric_detail, fabric_list

urlpatterns = [
    # This list endpoint powers the signed-in web dashboard and any future clients.
    path('list/', fabric_list, name='fabric-api-list'),
    path('add/', add_fabric, name='fabric-api-add'),
    path('<int:fabric_id>/', fabric_detail, name='fabric-api-detail'),
]
