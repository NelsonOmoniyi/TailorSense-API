"""Serializers used to expose fabric inventory data through the API."""

from rest_framework import serializers

from .models import Fabric


class FabricSerializer(serializers.ModelSerializer):
    """Convert fabric records into a safe JSON payload for authenticated clients."""

    class Meta:
        model = Fabric
        fields = [
            'id',
            'name',
            'category',
            'composition',
            'color',
            'weight_gsm',
            'price_per_meter',
            'stock_units',
            'supplier',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
