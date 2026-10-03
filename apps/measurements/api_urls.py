"""URL patterns for measurement catalog and profile APIs."""

from django.urls import path

from . import api_views

urlpatterns = [
    path('types/', api_views.measurement_types, name='measurement-api-types'),
    path('standards/', api_views.standard_measurement_sets, name='measurement-api-standards'),
    path('profiles/', api_views.measurement_profiles, name='measurement-api-profiles'),
]