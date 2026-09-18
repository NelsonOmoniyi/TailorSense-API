from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Fabric
from .serializers import FabricSerializer


class FabricViewSet(viewsets.ModelViewSet):
    queryset = Fabric.objects.all()
    serializer_class = FabricSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
