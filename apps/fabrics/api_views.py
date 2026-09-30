"""API views for authenticated fabric inventory access."""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.auth import authenticated_required, get_authenticated_user
from .models import Fabric
from .serializers import FabricSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authenticated_required
def fabric_list(request):
    """Return every available fabric for signed-in users using the shared auth gate."""
    user = get_authenticated_user(request)
    if user is None:
        return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

    fabrics = Fabric.objects.order_by('fabric_name')
    serializer = FabricSerializer(fabrics, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authenticated_required
def add_fabric(request):
    """Create one fabric record from either JSON or form-encoded API input."""
    user = get_authenticated_user(request)
    if user is None:
        return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

    serializer = FabricSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    fabric = serializer.save()
    return Response(FabricSerializer(fabric).data, status=status.HTTP_201_CREATED)
