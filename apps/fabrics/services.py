"""Shared helpers for linking the fabric and style catalogues."""

import json
from pathlib import Path

from apps.styles.models import Style, StyleFabric

from .models import Fabric


RECOMMENDATIONS_PATH = Path(__file__).resolve().parent / 'data' / 'style_fabric_recommendations.json'
AUTO_LINK_NOTE = 'Recommended for this style in the catalogue.'


def sync_style_fabric_recommendations():
    """Create links for exact catalogue-name matches without replacing manual links."""
    with RECOMMENDATIONS_PATH.open(encoding='utf-8') as recommendations_file:
        recommendations = json.load(recommendations_file)

    styles = {
        f'{style.garment.slug}/{style.slug}': style
        for style in Style.objects.select_related('garment')
    }
    fabrics = {
        fabric.fabric_name.casefold(): fabric
        for fabric in Fabric.objects.all()
    }
    missing_styles = set(recommendations) - set(styles)
    missing_fabrics = set()
    links_added = 0
    expected_pairs = set()

    for style_key, fabric_names in recommendations.items():
        style = styles.get(style_key)
        if style is None:
            continue
        for fabric_name in fabric_names:
            fabric = fabrics.get(fabric_name.casefold())
            if fabric is None:
                missing_fabrics.add(fabric_name)
                continue
            expected_pairs.add((style.pk, fabric.pk))
            _, created = StyleFabric.objects.get_or_create(
                style=style,
                fabric=fabric,
                defaults={
                    'suitability': StyleFabric.Suitability.GOOD,
                    'notes': AUTO_LINK_NOTE,
                    'is_active': True,
                },
            )
            links_added += int(created)

    stale_link_ids = [
        link_id
        for link_id, style_id, fabric_id in StyleFabric.objects.filter(
            notes=AUTO_LINK_NOTE
        ).values_list('id', 'style_id', 'fabric_id')
        if (style_id, fabric_id) not in expected_pairs
    ]
    links_removed = 0
    if stale_link_ids:
        _, links_removed = StyleFabric.objects.filter(id__in=stale_link_ids).delete()

    return {
        'links_added': links_added,
        'links_removed': links_removed,
        'missing_fabrics': tuple(sorted(missing_fabrics)),
        'missing_styles': tuple(sorted(missing_styles)),
    }
