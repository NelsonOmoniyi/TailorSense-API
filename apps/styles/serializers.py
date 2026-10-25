"""Validated JSON representations for the Styles API."""

from django.db import transaction
from rest_framework import serializers

from apps.fabrics.models import Fabric
from apps.measurements.models import MeasurementType
from .models import Garment, Occasion, Style, StyleFabric, StyleImage, StyleMeasurementRequirement


class GarmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Garment
        fields = ['id', 'name', 'slug', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class OccasionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Occasion
        fields = ['id', 'name', 'description']


class StyleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StyleImage
        fields = ['id', 'image', 'view_type', 'alt_text', 'is_primary', 'display_order', 'created_at']
        read_only_fields = ['id', 'created_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if data.get('image') and request:
            data['image'] = request.build_absolute_uri(data['image'])
        return data

    def update(self, instance, validated_data):
        replacement = validated_data.get('image')
        if replacement and instance.image:
            existing_name = instance.image.name
            # Reuse the same catalogue filename; deleting first prevents storage
            # backends from appending a collision suffix during the save.
            instance.image.storage.delete(existing_name)
            replacement.name = existing_name.rsplit('/', 1)[-1]
        return super().update(instance, validated_data)


class StyleFabricReadSerializer(serializers.ModelSerializer):
    fabric = serializers.SerializerMethodField()

    class Meta:
        model = StyleFabric
        fields = ['id', 'fabric', 'suitability', 'notes', 'is_active']

    def get_fabric(self, obj):
        return {'id': obj.fabric_id, 'fabric_name': obj.fabric.fabric_name}


class StyleMeasurementReadSerializer(serializers.ModelSerializer):
    measurement_type = serializers.SerializerMethodField()

    class Meta:
        model = StyleMeasurementRequirement
        fields = ['id', 'measurement_type', 'is_required', 'notes', 'display_order']

    def get_measurement_type(self, obj):
        item = obj.measurement_type
        return {'id': item.pk, 'name': item.name, 'code': item.code, 'unit': item.unit, 'category': item.category}


class StyleSerializer(serializers.ModelSerializer):
    garment = GarmentSerializer(read_only=True)
    garment_id = serializers.PrimaryKeyRelatedField(
        source='garment', queryset=Garment.objects.filter(is_active=True), write_only=True
    )
    occasions = OccasionSerializer(many=True, read_only=True)
    occasion_ids = serializers.PrimaryKeyRelatedField(
        source='occasions', queryset=Occasion.objects.all(), many=True, required=False, write_only=True
    )
    images = StyleImageSerializer(many=True, required=False)
    fabrics = StyleFabricReadSerializer(source='fabric_links', many=True, read_only=True)
    measurement_requirements = StyleMeasurementReadSerializer(many=True, read_only=True)

    class Meta:
        model = Style
        fields = [
            'id', 'name', 'slug', 'garment', 'garment_id', 'gender', 'category', 'description',
            'silhouette', 'fit_type', 'occasions', 'occasion_ids', 'complexity', 'is_active',
            'images', 'fabrics', 'measurement_requirements', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_slug(self, value):
        garment = self.initial_data.get('garment_id')
        if garment is None and self.instance:
            garment = self.instance.garment_id
        if garment is None:
            return value
        queryset = Style.objects.filter(slug=value, garment_id=garment)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('A style with this slug already exists.')
        return value

    @transaction.atomic
    def create(self, validated_data):
        occasions = validated_data.pop('occasions', [])
        images = validated_data.pop('images', [])
        style = Style.objects.create(**validated_data)
        style.occasions.set(occasions)
        for image in images:
            StyleImage.objects.create(style=style, **image)
        return style

    @transaction.atomic
    def update(self, instance, validated_data):
        occasions = validated_data.pop('occasions', None)
        images = validated_data.pop('images', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if occasions is not None:
            instance.occasions.set(occasions)
        if images is not None:
            instance.images.all().delete()
            for image in images:
                StyleImage.objects.create(style=instance, **image)
        return instance


class StyleFabricWriteSerializer(serializers.ModelSerializer):
    fabric_id = serializers.PrimaryKeyRelatedField(source='fabric', queryset=Fabric.objects.all(), write_only=True)

    class Meta:
        model = StyleFabric
        fields = ['id', 'fabric_id', 'suitability', 'notes', 'is_active']
        read_only_fields = ['id']


class StyleMeasurementWriteSerializer(serializers.ModelSerializer):
    measurement_type_id = serializers.PrimaryKeyRelatedField(
        source='measurement_type', queryset=MeasurementType.objects.all(), write_only=True
    )

    class Meta:
        model = StyleMeasurementRequirement
        fields = ['id', 'measurement_type_id', 'is_required', 'notes', 'display_order']
        read_only_fields = ['id']
