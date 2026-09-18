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

    fabrics = Fabric.objects.order_by('name')
    serializer = FabricSerializer(fabrics, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
