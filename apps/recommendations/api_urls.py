"""Versioned Recommendations API routes."""

from django.urls import path

from .api_views import RecommendationView

app_name = 'recommendations_api'

urlpatterns = [
    path('', RecommendationView.as_view(), name='recommendations'),
]
