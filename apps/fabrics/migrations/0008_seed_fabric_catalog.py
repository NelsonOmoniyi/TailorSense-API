"""Seed the fabric catalogue used by the TailorSense workspace."""

import json
from pathlib import Path

from django.core.management.color import no_style
from django.db import migrations


def seed_fabrics(apps, schema_editor):
    Fabric = apps.get_model('fabrics', 'Fabric')
    database = schema_editor.connection.alias
    if Fabric.objects.using(database).exists():
        return

    rows = json.loads(Path(__file__).with_name('fabric_catalog_seed.json').read_text(encoding='utf-8'))

    for row in rows:
        row = dict(row)
        seed_id = row.pop('id')
        fabric_name = row.pop('fabric_name')
        manager = Fabric.objects.using(database)
        fabric = manager.filter(fabric_name=fabric_name).first()
        if fabric is None:
            manager.create(pk=seed_id, fabric_name=fabric_name, **row)

    statements = schema_editor.connection.ops.sequence_reset_sql(no_style(), [Fabric])
    with schema_editor.connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


class Migration(migrations.Migration):
    dependencies = [
        ('fabrics', '0007_fabric_image'),
    ]

    operations = [
        migrations.RunPython(seed_fabrics, migrations.RunPython.noop),
    ]
