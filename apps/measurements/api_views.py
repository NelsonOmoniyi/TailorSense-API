"""Authenticated API endpoints for measurement types and user profiles."""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.auth import authenticated_required, get_authenticated_user
from .models import MeasurementProfile, MeasurementType, StandardMeasurementSet
from .serializers import (
    MeasurementProfileCreateSerializer,
    MeasurementProfileSerializer,
    StandardMeasurementSetSerializer,
    MeasurementTypeSerializer,
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authenticated_required
def measurement_types(request):
    """Return the shared catalog used to label and validate profile entries."""
    if get_authenticated_user(request) is None:
        return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

    serializer = MeasurementTypeSerializer(MeasurementType.objects.all(), many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authenticated_required
def standard_measurement_sets(request):
    """Return globally shared field templates without requiring a user profile."""
    if get_authenticated_user(request) is None:
        return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

    standards = StandardMeasurementSet.objects.prefetch_related(
        'requirements__measurement_type'
    )
    serializer = StandardMeasurementSetSerializer(standards, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authenticated_required
def measurement_profiles(request):
    """List only the signed-in user's profiles or atomically create a profile."""
    user = get_authenticated_user(request)
    if user is None:
        return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        profiles = (
            MeasurementProfile.objects
            .filter(user=user)
            .prefetch_related('measurements__measurement_type')
        )
        serializer = MeasurementProfileSerializer(profiles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = MeasurementProfileCreateSerializer(
        data=request.data,
        context={'request': request},
    )
    serializer.is_valid(raise_exception=True)
    profile = serializer.save()
    response_serializer = MeasurementProfileSerializer(profile)
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)