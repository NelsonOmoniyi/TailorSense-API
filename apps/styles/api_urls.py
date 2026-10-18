"""Versioned catalogue endpoints for garments, styles, and style requirements."""

from django.urls import path

from . import api_views

app_name = 'styles_api'

urlpatterns = [
    path('garments/', api_views.GarmentListCreateView.as_view(), name='garment-list'),
    path('garments/<int:pk>/', api_views.GarmentDetailView.as_view(), name='garment-detail'),
    path('styles/', api_views.StyleListCreateView.as_view(), name='style-list'),
    path('styles/<int:pk>/', api_views.StyleDetailView.as_view(), name='style-detail'),
    path('styles/<int:style_id>/images/', api_views.StyleImageListCreateView.as_view(), name='style-images'),
    path('styles/<int:style_id>/fabrics/', api_views.StyleFabricManageView.as_view(), name='style-fabrics'),
    path('styles/<int:style_id>/measurements/', api_views.StyleMeasurementManageView.as_view(), name='style-measurements'),
]
