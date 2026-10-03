"""JSON serializers for the Measurements API."""

from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from .models import (
    Measurement,
    MeasurementProfile,
    MeasurementType,
    MeasurementUnit,
    StandardMeasurementSet,
)


class MeasurementTypeSerializer(serializers.ModelSerializer):
    """Expose stable type codes so clients never depend on database IDs."""

    class Meta:
        model = MeasurementType
        fields = ['id', 'name', 'code', 'category', 'description', 'unit', 'gender', 'is_core']


class MeasurementSerializer(serializers.ModelSerializer):
    """Return a measurement row with its reusable type definition."""

    measurement_type = MeasurementTypeSerializer(read_only=True)

    class Meta:
        model = Measurement
        fields = ['id', 'measurement_type', 'value', 'unit', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class MeasurementProfileSerializer(serializers.ModelSerializer):
    """Read representation for a profile and its normalized measurement rows."""

    measurements = MeasurementSerializer(many=True, read_only=True)

    class Meta:
        model = MeasurementProfile
        fields = ['id', 'name', 'gender', 'unit', 'created_at', 'updated_at', 'measurements']
        read_only_fields = ['id', 'created_at', 'updated_at']


class StandardMeasurementRequirementSerializer(serializers.Serializer):
    measurement_type = MeasurementTypeSerializer(read_only=True)
    is_required = serializers.BooleanField()


class StandardMeasurementSetSerializer(serializers.ModelSerializer):
    """Read-only shared measurement fields, not a user's body-value profile."""

    requirements = StandardMeasurementRequirementSerializer(many=True, read_only=True)

    class Meta:
        model = StandardMeasurementSet
        fields = ['id', 'name', 'gender', 'context', 'description', 'requirements']


class MeasurementEntryCreateSerializer(serializers.Serializer):
    """Accept a stable measurement type code plus one positive numeric value."""

    measurement_type = serializers.SlugRelatedField(
        slug_field='code',
        queryset=MeasurementType.objects.all(),
    )
    value = serializers.DecimalField(max_digits=7, decimal_places=2, min_value=Decimal('0.01'))
    unit = serializers.ChoiceField(choices=MeasurementUnit.choices, required=False)


class MeasurementProfileCreateSerializer(serializers.ModelSerializer):
    """Create one profile and all supplied measurement rows as one transaction."""

    measurements = MeasurementEntryCreateSerializer(many=True)

    class Meta:
        model = MeasurementProfile
        fields = ['name', 'gender', 'unit', 'measurements']

    def validate_measurements(self, measurements):
        if not measurements:
            raise serializers.ValidationError('Add at least one measurement.')

        type_ids = [entry['measurement_type'].pk for entry in measurements]
        if len(type_ids) != len(set(type_ids)):
            raise serializers.ValidationError('A measurement type can only be included once per profile.')
        return measurements

    def validate(self, attrs):
        """Resolve units from the profile for lengths and from the type for weight."""
        profile_unit = attrs.get('unit', MeasurementProfile._meta.get_field('unit').default)
        for entry in attrs['measurements']:
            measurement_type = entry['measurement_type']
            allowed_units = {'kg', 'lb'} if measurement_type.unit in {'kg', 'lb'} else {'cm', 'in'}
            requested_unit = entry.get('unit')
            if requested_unit and requested_unit not in allowed_units:
                raise serializers.ValidationError({
                    'measurements': f"{measurement_type.name} must use one of: {', '.join(sorted(allowed_units))}."
                })
            entry['unit'] = requested_unit or (
                measurement_type.unit if measurement_type.unit in {'kg', 'lb'} else profile_unit
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        measurement_entries = validated_data.pop('measurements')
        profile = MeasurementProfile.objects.create(
            user=self.context['request'].user,
            **validated_data,
        )
        Measurement.objects.bulk_create([
            Measurement(
                profile=profile,
                measurement_type=entry['measurement_type'],
                value=entry['value'],
                unit=entry['unit'],
            )
            for entry in measurement_entries
        ])
        return profile