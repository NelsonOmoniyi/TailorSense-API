"""Serializers used to expose fabric inventory data through the API."""

from rest_framework import serializers

from .models import Fabric


class FabricSerializer(serializers.ModelSerializer):
    """Convert fabric records into a safe JSON payload for authenticated clients."""

    class Meta:
        model = Fabric
        fields = [
            'id',
            'fabric_name',
            'fiber_category',
            'fiber',
            'fabric_type',
            'composition',
            'construction',
            'weight',
            'stretch',
            'structure',
            'breathability',
            'opacity',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'fabric_name': {'required': True, 'allow_blank': False},
            'fiber_category': {'required': True, 'allow_blank': False},
            'fiber': {'required': True, 'allow_blank': False},
            'fabric_type': {'required': True, 'allow_blank': False},
            'composition': {'required': True, 'allow_blank': False},
            'construction': {'required': True, 'allow_blank': False},
            'weight': {'required': True, 'allow_blank': False},
            'stretch': {'required': True},
            'structure': {'required': True, 'allow_blank': False},
            'breathability': {'required': True},
            'opacity': {'required': True},
        }
