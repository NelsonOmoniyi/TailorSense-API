from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import FabricViewSet

router = DefaultRouter()
router.register(r'', FabricViewSet, basename='fabric')

urlpatterns = [
    path('', include(router.urls)),
]
