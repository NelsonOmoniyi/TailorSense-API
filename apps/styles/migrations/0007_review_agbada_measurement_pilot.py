"""Record the Agbada checklist review and resolve confirmed style conditions."""

from datetime import datetime, timezone

from django.db import migrations


REVIEWER = 'Nelson Omoniyi - Board of Trustees, TairlorSense LTD'
REVIEWED_AT = datetime(2026, 11, 1, tzinfo=timezone.utc)
CONFIRMATION = (
    'Applicability confirmed by Nelson Omoniyi on 2026-11-01: '
    'all active Agbada styles include this feature.'
)


def record_agbada_review(apps, schema_editor):
    database = schema_editor.connection.alias
    Style = apps.get_model('styles', 'Style')
    Requirement = apps.get_model('styles', 'StyleMeasurementRequirement')

    styles = Style.objects.using(database).filter(
        garment__slug='agbada',
        is_active=True,
    )
    styles.update(
        measurement_specification_status='reviewed',
        measurement_specification_reviewed_by=REVIEWER,
        measurement_specification_reviewed_at=REVIEWED_AT,
    )
    styles.filter(measurement_specification_source='').update(
        measurement_specification_source=(
            'User-provided Agbada checklist; individual sources are recorded on each requirement.'
        ),
    )

    conditional_requirements = Requirement.objects.using(database).filter(
        style__in=styles,
        measurement_type__code__in=[
            'thigh_circumference',
            'embroidery_area_width',
            'embroidery_area_depth',
        ],
    )
    for requirement in conditional_requirements:
        original_condition = requirement.condition.strip()
        if original_condition:
            confirmation_note = (
                f'{CONFIRMATION} Original condition: {original_condition}'
            )
            if confirmation_note not in requirement.notes:
                requirement.notes = '; '.join(
                    part for part in [requirement.notes.strip(), confirmation_note] if part
                )
            requirement.condition = ''
            requirement.save(using=database, update_fields=['condition', 'notes'])


class Migration(migrations.Migration):

    dependencies = [
        ('styles', '0006_agbada_measurement_pilot'),
    ]

    operations = [
        migrations.RunPython(record_agbada_review, migrations.RunPython.noop),
    ]
