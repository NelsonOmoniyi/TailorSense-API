"""Authenticated read and write endpoints for the style catalogue."""

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions

from apps.users.auth import get_authenticated_user
from .models import Garment, Style, StyleFabric, StyleImage, StyleMeasurementRequirement
from .serializers import (
    GarmentSerializer, StyleFabricReadSerializer, StyleFabricWriteSerializer, StyleImageSerializer,
    StyleMeasurementReadSerializer, StyleMeasurementWriteSerializer, StyleSerializer,
)


class ProjectSessionPermission(permissions.BasePermission):
    """Apply TailorSense's session identity check to session and JWT callers."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # JWT requests have no project session hash; rely on DRF's verified JWT.
        if request.auth is not None:
            return True
        return get_authenticated_user(request) is not None


class AuthenticatedAPIViewMixin:
    permission_classes = [ProjectSessionPermission]


class GarmentListCreateView(AuthenticatedAPIViewMixin, generics.ListCreateAPIView):
    serializer_class = GarmentSerializer

    def get_queryset(self):
        return Garment.objects.filter(is_active=True)


class GarmentDetailView(AuthenticatedAPIViewMixin, generics.RetrieveAPIView):
    serializer_class = GarmentSerializer
    queryset = Garment.objects.filter(is_active=True)


class StyleListCreateView(AuthenticatedAPIViewMixin, generics.ListCreateAPIView):
    serializer_class = StyleSerializer

    def get_queryset(self):
        queryset = Style.objects.filter(garment__is_active=True).select_related('garment').prefetch_related(
            'occasions', 'images', 'fabric_links__fabric',
            'measurement_requirements__measurement_type',
        )
        params = self.request.query_params
        if params.get('active') is not None:
            queryset = queryset.filter(is_active=params.get('active').lower() in {'true', '1', 'yes'})
        else:
            queryset = queryset.filter(is_active=True)
        for param, field in [('garment', 'garment__slug'), ('gender', 'gender')]:
            if params.get(param):
                queryset = queryset.filter(**{field: params[param]})
        if params.get('occasion'):
            queryset = queryset.filter(occasions__name__iexact=params['occasion'])
        if params.get('q'):
            queryset = queryset.filter(name__icontains=params['q'].strip())
        return queryset.distinct()


class StyleDetailView(AuthenticatedAPIViewMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StyleSerializer
    queryset = Style.objects.select_related('garment').prefetch_related(
        'occasions', 'images', 'fabric_links__fabric', 'measurement_requirements__measurement_type',
    )


class StyleImageListCreateView(AuthenticatedAPIViewMixin, generics.ListCreateAPIView):
    """List images or upload one image for a style using configured storage."""

    serializer_class = StyleImageSerializer

    def get_queryset(self):
        return StyleImage.objects.filter(style_id=self.kwargs['style_id'])

    def perform_create(self, serializer):
        style = get_object_or_404(Style, pk=self.kwargs['style_id'])
        serializer.save(style=style)


class StyleFabricManageView(AuthenticatedAPIViewMixin, generics.ListCreateAPIView):
    """List suitable fabrics or attach a fabric to a style."""

    def get_queryset(self):
        return StyleFabric.objects.filter(style_id=self.kwargs['style_id']).select_related('fabric')

    def get_serializer_class(self):
        return StyleFabricReadSerializer if self.request.method == 'GET' else StyleFabricWriteSerializer

    def perform_create(self, serializer):
        style = get_object_or_404(Style, pk=self.kwargs['style_id'])
        serializer.save(style=style)


class StyleMeasurementManageView(AuthenticatedAPIViewMixin, generics.ListCreateAPIView):
    """List measurement requirements or attach a measurement type to a style."""

    def get_queryset(self):
        return StyleMeasurementRequirement.objects.filter(
            style_id=self.kwargs['style_id']
        ).select_related('measurement_type')

    def get_serializer_class(self):
        return StyleMeasurementReadSerializer if self.request.method == 'GET' else StyleMeasurementWriteSerializer

    def perform_create(self, serializer):
        style = get_object_or_404(Style, pk=self.kwargs['style_id'])
        serializer.save(style=style)
