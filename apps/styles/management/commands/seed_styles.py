"""Sync the approved seven-category style catalogue into the database."""

import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.styles.models import Garment, Occasion, Style


CATALOG_PATH = Path(__file__).resolve().parents[2] / 'data' / 'core_style_catalog.json'
LEGACY_SLUGS = {
    'women-s-flowing-trousers': 'womens-flowing-trousers',
    'women-s-wide-base-trousers': 'womens-wide-base-trousers',
}


class Command(BaseCommand):
    help = 'Create or update the approved garment categories and their catalogue styles.'

    @transaction.atomic
    def handle(self, *args, **options):
        with CATALOG_PATH.open(encoding='utf-8') as catalog_file:
            catalog = json.load(catalog_file)

        active_garment_slugs = []
        style_count = 0
        occasions = {
            name: Occasion.objects.get_or_create(name=name)[0]
            for name in ('Casual', 'Formal', 'Work')
        }

        # Earlier imports converted the apostrophe in "Women's" into a dash.
        # Normalize those sample slugs in place before syncing the corrected slugs.
        for old_slug, new_slug in LEGACY_SLUGS.items():
            old_styles = Style.objects.filter(garment__slug='trousers', slug=old_slug)
            if Style.objects.filter(garment__slug='trousers', slug=new_slug).exists():
                old_styles.update(is_active=False)
            else:
                old_styles.update(slug=new_slug)

        for category in catalog['categories']:
            garment, _ = Garment.objects.update_or_create(
                slug=category['slug'],
                defaults={
                    'name': category['name'],
                    'description': category['description'],
                    'is_active': True,
                },
            )
            active_garment_slugs.append(category['slug'])

            for item in category['styles']:
                style, _ = Style.objects.update_or_create(
                    slug=item['slug'],
                    garment=garment,
                    defaults={
                        'name': item['name'],
                        'description': item['description'],
                        'garment': garment,
                        'gender': item['gender'],
                        'category': item['category'],
                        'silhouette': item['silhouette'],
                        'fit_type': item['fit_type'],
                        'complexity': item['complexity'],
                        'is_active': item['is_active'],
                    },
                )
                style.occasions.set([occasions[item['occasion']]])
                style_count += 1

        # Keep old or manually created records for auditability, but archive
        # styles attached to categories outside the approved active catalogue.
        Garment.objects.exclude(slug__in=active_garment_slugs).update(is_active=False)
        Style.objects.filter(garment__is_active=False).update(is_active=False)

        self.stdout.write(self.style.SUCCESS(
            f'Catalogue synced: {len(active_garment_slugs)} active categories and {style_count} active styles.'
        ))
