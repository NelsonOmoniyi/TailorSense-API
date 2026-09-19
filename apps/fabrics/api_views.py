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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authenticated_required
def add_fabric(request):
    """Add fabrics to DB for signed-in users using the shared auth gate."""
    user = get_authenticated_user(request)
    if user is None:
        return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
    if request.method == 'POST':
            fabric_name = request.POST.get('fabric_name', '').strip()
            fiber_category = request.POST.get('fiber_category', '').strip()
            fiber = request.POST.get('fiber', '').strip()
            fabric_type = request.POST.get('fabric_type', '').strip()
            composition = request.POST.get('composition', '').strip()
            construction = request.POST.get('construction', '').strip()
            weight = request.POST.get('weight', '').strip()
            stretch = request.POST.get('stretch', '').strip()
            structure = request.POST.get('structure', '').strip()
            breathability = request.POST.get('breathability', '').strip()
            opacity = request.POST.get('opacity', '').strip()
    
            if not all((fabric_name, fiber_category, fiber, fabric_type, composition, construction, weight, stretch, structure, breathability, opacity)):
                error = 'All fields are required.'
                return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Create the fabric record.
                Fabric.objects.create(
                    fabric_name=fabric_name,
                    fiber_category=fiber_category,
                    fiber=fiber,
                    fabric_type=fabric_type,
                    composition=composition,
                    construction=construction,
                    weight=weight,
                    stretch=stretch,
                    structure=structure,
                    breathability=breathability,
                    opacity=opacity
                )
    fabrics = Fabric.objects.order_by('fabric_name')
    serializer = FabricSerializer(fabrics, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)