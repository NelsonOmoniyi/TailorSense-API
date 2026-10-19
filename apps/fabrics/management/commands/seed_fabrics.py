"""Load the TailorSense fabric catalogue and attach known style recommendations."""

import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from ...models import Fabric
from ...services import sync_style_fabric_recommendations


DATA_DIR = Path(__file__).resolve().parents[2] / 'data'
FABRIC_CATALOG_PATH = DATA_DIR / 'core_fabrics.json'
RECOMMENDATIONS_PATH = DATA_DIR / 'style_fabric_recommendations.json'


class Command(BaseCommand):
    help = 'Create or update the fabric catalogue and link styles to listed fabrics.'

    @transaction.atomic
    def handle(self, *args, **options):
        with FABRIC_CATALOG_PATH.open(encoding='utf-8') as catalog_file:
            catalog = json.load(catalog_file)
        with RECOMMENDATIONS_PATH.open(encoding='utf-8') as recommendations_file:
            recommendations = json.load(recommendations_file)
        fabrics = {}
        for row in catalog:
            name, fiber_category, drape, weight, stretch, breathability, opacity = row
            fabric, _ = Fabric.objects.update_or_create(
                fabric_name=name,
                defaults={
                    'fiber_category': fiber_category,
                    'drape': drape,
                    'weight': weight,
                    'stretch': stretch,
                    'breathability': breathability,
                    'opacity': opacity,
                },
            )
            fabrics[name.casefold()] = fabric

        # The style table names additional fabrics without describing their
        # properties. Add those records so every listed recommendation can link
        # to a real Fabric row, leaving unprovided properties blank for review.
        recommendation_names = {
            fabric_name
            for fabric_names in recommendations.values()
            for fabric_name in fabric_names
        }
        existing_names = {
            name.casefold(): name
            for name in Fabric.objects.values_list('fabric_name', flat=True)
        }
        supplemental_count = 0
        for name in sorted(recommendation_names):
            if name.casefold() in existing_names:
                continue
            Fabric.objects.create(
                fabric_name=name,
                fiber_category='',
                weight='',
                stretch='',
                drape='',
                breathability='',
                opacity='',
            )
            existing_names[name.casefold()] = name
            supplemental_count += 1

        link_summary = sync_style_fabric_recommendations()

        self.stdout.write(self.style.SUCCESS(
            f'Fabric catalogue synced: {len(fabrics)} supplied fabrics and '
            f'{supplemental_count} recommendation fabrics with unspecified properties; '
            f'{link_summary["links_added"]} links added and '
            f'{link_summary["links_removed"]} obsolete catalogue links removed.'
        ))
        if link_summary['missing_fabrics']:
            self.stdout.write(self.style.WARNING(
                f'{len(link_summary["missing_fabrics"])} recommendation names were not in the supplied fabric list '
                f'and were skipped: {", ".join(link_summary["missing_fabrics"])}'
            ))
        if link_summary['missing_styles']:
            self.stdout.write(self.style.WARNING(
                f'{len(link_summary["missing_styles"])} recommendation rows have no matching style yet.'
            ))
