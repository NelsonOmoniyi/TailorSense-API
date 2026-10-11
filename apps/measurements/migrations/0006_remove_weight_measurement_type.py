"""Remove the body-weight measurement type.

Weight is not a tailoring measurement: a tape measure only captures linear
dimensions, and no pattern draft uses mass. The 0005 seed added it to every
standard template, so this migration detaches it from those templates and then
deletes the type itself.
"""

from django.db import migrations


def remove_weight_type(apps, schema_editor):
    MeasurementType = apps.get_model('measurements', 'MeasurementType')
    Requirement = apps.get_model('measurements', 'StandardMeasurementRequirement')
    Measurement = apps.get_model('measurements', 'Measurement')

    weight_type = MeasurementType.objects.filter(code='weight').first()
    if weight_type is None:
        return

    # Detach from every standard template before deleting the type it references.
    Requirement.objects.filter(measurement_type=weight_type).delete()

    # Measurement.measurement_type is PROTECT, so clear any saved values first.
    Measurement.objects.filter(measurement_type=weight_type).delete()

    weight_type.delete()


class Migration(migrations.Migration):
    dependencies = [
        ('measurements', '0005_seed_standard_measurement_sets'),
    ]

    operations = [
        migrations.RunPython(remove_weight_type, migrations.RunPython.noop),
    ]
