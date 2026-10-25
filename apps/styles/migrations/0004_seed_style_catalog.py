"""Seed the style catalogue and its image and recommendation relationships."""

import json
from pathlib import Path

from django.core.management.color import no_style
from django.db import migrations


def seed_styles(apps, schema_editor):
    database = schema_editor.connection.alias
    Garment = apps.get_model('styles', 'Garment')
    Occasion = apps.get_model('styles', 'Occasion')
    Style = apps.get_model('styles', 'Style')
    StyleImage = apps.get_model('styles', 'StyleImage')
    StyleFabric = apps.get_model('styles', 'StyleFabric')
    StyleMeasurementRequirement = apps.get_model('styles', 'StyleMeasurementRequirement')
    Fabric = apps.get_model('fabrics', 'Fabric')
    MeasurementType = apps.get_model('measurements', 'MeasurementType')

    if Style.objects.using(database).exists():
        return

    catalog = json.loads(Path(__file__).with_name('style_catalog_seed.json').read_text(encoding='utf-8'))

    garment_by_seed_id = {}
    for item in catalog['garments']:
        fields = {key: value for key, value in item.items() if key not in {'id', 'created_at', 'updated_at'}}
        fields['id'] = item['id']
        garment, _ = Garment.objects.using(database).get_or_create(slug=item['slug'], defaults=fields)
        garment_by_seed_id[item['id']] = garment

    occasion_by_seed_id = {}
    for item in catalog['occasions']:
        fields = {key: value for key, value in item.items() if key not in {'id'}}
        fields['id'] = item['id']
        occasion, _ = Occasion.objects.using(database).get_or_create(name=item['name'], defaults=fields)
        occasion_by_seed_id[item['id']] = occasion

    style_by_seed_id = {}
    for item in catalog['styles']:
        garment = garment_by_seed_id[item['garment_id']]
        fields = {
            key: value for key, value in item.items()
            if key not in {'id', 'garment_id', 'occasion_ids', 'created_at', 'updated_at'}
        }
        fields['id'] = item['id']
        style, _ = Style.objects.using(database).get_or_create(
            garment_id=garment.pk, slug=item['slug'], defaults=fields,
        )
        style_by_seed_id[item['id']] = style
        style.occasions.set([occasion_by_seed_id[key] for key in item['occasion_ids']])

    for item in catalog['images']:
        style = style_by_seed_id[item['style_id']]
        fields = {key: value for key, value in item.items() if key not in {'id', 'style_id'}}
        fields['style_id'] = style.pk
        StyleImage.objects.using(database).get_or_create(pk=item['id'], defaults=fields)

    fabrics_by_seed_id = {}
    fabric_rows = json.loads(
        Path(__file__).parents[2].joinpath('fabrics', 'migrations', 'fabric_catalog_seed.json').read_text(encoding='utf-8')
    )
    # Resolve the original fabric IDs through their stable names, including databases
    # where the catalogue existed before this seed migration was installed.
    for item in fabric_rows:
        fabric = Fabric.objects.using(database).filter(fabric_name=item['fabric_name']).first()
        if fabric is not None:
            fabrics_by_seed_id[item['id']] = fabric

    for item in catalog['style_fabrics']:
        style = style_by_seed_id[item['style_id']]
        fabric = fabrics_by_seed_id.get(item['fabric_id'])
        if fabric is None:
            continue
        fields = {key: value for key, value in item.items() if key not in {'id', 'style_id', 'fabric_id'}}
        fields['id'] = item['id']
        StyleFabric.objects.using(database).get_or_create(
            style_id=style.pk, fabric_id=fabric.pk, defaults=fields,
        )

    for item in catalog['measurement_requirements']:
        style = style_by_seed_id[item['style_id']]
        measurement_type = MeasurementType.objects.using(database).filter(pk=item['measurement_type_id']).first()
        if measurement_type is None:
            continue
        fields = {
            key: value for key, value in item.items()
            if key not in {'id', 'style_id', 'measurement_type_id'}
        }
        fields['id'] = item['id']
        StyleMeasurementRequirement.objects.using(database).get_or_create(
            style_id=style.pk, measurement_type_id=measurement_type.pk, defaults=fields,
        )

    seeded_models = [Garment, Occasion, Style, StyleImage, StyleFabric, StyleMeasurementRequirement]
    statements = schema_editor.connection.ops.sequence_reset_sql(no_style(), seeded_models)
    with schema_editor.connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


class Migration(migrations.Migration):
    dependencies = [
        ('fabrics', '0008_seed_fabric_catalog'),
        ('measurements', '0007_alter_measurement_unit_alter_measurementtype_unit'),
        ('styles', '0003_alter_style_slug_style_unique_style_slug_per_garment'),
    ]

    operations = [
        migrations.RunPython(seed_styles, migrations.RunPython.noop),
    ]
