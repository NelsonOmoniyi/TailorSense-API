"""Database coordination for style recommendation requests."""

from django.db.models import Prefetch

from apps.styles.models import Style, StyleFabric, StyleImage, StyleMeasurementRequirement

from .engine import rank_styles


def get_recommendations(profile, fabric, category, occasion=None, limit=10):
    """Load scoped candidates and delegate eligibility and ranking to the engine."""
    matching_links = StyleFabric.objects.filter(
        fabric=fabric,
        is_active=True,
    ).exclude(suitability=StyleFabric.Suitability.UNSUITABLE)

    styles = (
        Style.objects.filter(
            is_active=True,
            garment=category,
            garment__is_active=True,
            pk__in=matching_links.values('style_id'),
        )
        .select_related('garment')
        .prefetch_related(
            Prefetch(
                'fabric_links',
                queryset=matching_links.select_related('fabric'),
            ),
            Prefetch(
                'measurement_requirements',
                queryset=StyleMeasurementRequirement.objects.select_related('measurement_type'),
            ),
            'occasions',
            Prefetch(
                'images',
                queryset=StyleImage.objects.order_by('-is_primary', 'display_order', 'pk'),
            ),
        )
    )
    measurement_type_ids = set(
        profile.measurements.values_list('measurement_type_id', flat=True)
    )
    ranked, missing_required = rank_styles(
        styles,
        measurement_type_ids,
        profile_gender=profile.gender,
        occasion=occasion,
    )
    return ranked[:limit], missing_required
