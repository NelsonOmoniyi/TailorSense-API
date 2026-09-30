from django.urls import path

from apps.core import views as core_views

urlpatterns = [
    # Core owns the UI and calls this app's API; this app owns the fabric URL namespace.
    path('', core_views.fabric_dashboard, name='fabrics-dashboard'),
    path('add/', core_views.add_fabric, name='add-fabric'),
]
