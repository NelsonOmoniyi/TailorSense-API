"""Request validation and response serialization for Recommendations API."""

from collections.abc import Mapping

from rest_framework import serializers

from apps.fabrics.models import Fabric
from apps.measurements.models import MeasurementProfile
from apps.styles.models import Garment, Occasion
from apps.styles.serializers import StyleImageSerializer


class RecommendationRequestSerializer(serializers.Serializer):
    measurement_profile_id = serializers.PrimaryKeyRelatedField(
        queryset=MeasurementProfile.objects.none(),
    )
    fabric_id = serializers.PrimaryKeyRelatedField(queryset=Fabric.objects.all())
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Garment.objects.filter(is_active=True),
    )
    occasion = serializers.CharField(required=False, allow_blank=False, trim_whitespace=True)
    limit = serializers.IntegerField(min_value=1, max_value=20, required=False, default=10)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            self.fields['measurement_profile_id'].queryset = MeasurementProfile.objects.filter(user=user)

    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            unsupported = set(data) - set(self.fields)
            if unsupported:
                raise serializers.ValidationError({
                    key: 'This field is not supported.'
                    for key in sorted(unsupported)
                })
        return super().to_internal_value(data)

    def validate_occasion(self, value):
        matches = list(Occasion.objects.filter(name__iexact=value).order_by('pk')[:2])
        if len(matches) != 1:
            raise serializers.ValidationError('Select one unambiguous recorded occasion name.')
        return matches[0]


class RecommendationResultSerializer(serializers.Serializer):
    style_id = serializers.IntegerField(source='style.pk')
    name = serializers.CharField(source='style.name')
    description = serializers.CharField(source='style.description')
    score = serializers.FloatField()
    reasons = serializers.ListField(child=serializers.CharField())
    missing_measurements = serializers.ListField(child=serializers.DictField())
    images = StyleImageSerializer(source='style.images', many=True)
