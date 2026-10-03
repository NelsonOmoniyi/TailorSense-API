from django.db import migrations


def seed_standard_measurements(apps, schema_editor):
    """Create shared field templates; these rows contain no user's body values."""
    MeasurementType = apps.get_model('measurements', 'MeasurementType')
    StandardMeasurementSet = apps.get_model('measurements', 'StandardMeasurementSet')
    Requirement = apps.get_model('measurements', 'StandardMeasurementRequirement')

    weight_type, _ = MeasurementType.objects.get_or_create(
        code='weight',
        defaults={
            'name': 'Weight',
            'category': 'body',
            'description': 'Body weight.',
            'unit': 'kg',
            'gender': '',
            'is_core': True,
        },
    )

    sets = [
        {
            'gender': 'male',
            'context': 'casual',
            'name': 'Casual (Male)',
            'description': 'Shared field template for a casual male fit. Add your own values in a custom profile.',
            'required': ('height', 'weight', 'shoulder_width', 'chest', 'waist', 'full_hip', 'sleeve_length', 'inseam'),
            'optional': ('neck_circumference', 'shirt_length'),
        },
        {
            'gender': 'male',
            'context': 'corporate',
            'name': 'Corporate (Male)',
            'description': 'Shared field template for corporate shirts and trousers. Add your own values in a custom profile.',
            'required': ('height', 'weight', 'neck_circumference', 'shoulder_width', 'chest', 'waist', 'sleeve_length', 'shirt_length', 'inseam'),
            'optional': ('full_hip',),
        },
        {
            'gender': 'female',
            'context': 'casual',
            'name': 'Casual (Female)',
            'description': 'Shared field template for casual clothing. Add your own values in a custom profile.',
            'required': ('height', 'weight', 'shoulder_width', 'bust', 'waist', 'full_hip', 'sleeve_length', 'dress_length'),
            'optional': ('neck_circumference',),
        },
        {
            'gender': 'female',
            'context': 'corporate',
            'name': 'Corporate (Female)',
            'description': 'Shared field template for corporate clothing. Add your own values in a custom profile.',
            'required': ('height', 'weight', 'neck_circumference', 'shoulder_width', 'bust', 'waist', 'full_hip', 'sleeve_length', 'dress_length'),
            'optional': ('armhole', 'bicep', 'wrist', 'front_neck_depth', 'back_neck_depth', 'sleeve_opening'),
        },
    ]

    for standard_data in sets:
        standard, _ = StandardMeasurementSet.objects.get_or_create(
            gender=standard_data['gender'],
            context=standard_data['context'],
            defaults={
                'name': standard_data['name'],
                'description': standard_data['description'],
            },
        )
        for code in standard_data['required']:
            measurement_type = weight_type if code == 'weight' else MeasurementType.objects.get(code=code)
            Requirement.objects.update_or_create(
                standard_set=standard,
                measurement_type=measurement_type,
                defaults={'is_required': True},
            )
        for code in standard_data['optional']:
            measurement_type = MeasurementType.objects.get(code=code)
            Requirement.objects.update_or_create(
                standard_set=standard,
                measurement_type=measurement_type,
                defaults={'is_required': False},
            )


class Migration(migrations.Migration):
    dependencies = [
        ('measurements', '0004_alter_measurement_unit_alter_measurementtype_unit_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_standard_measurements, migrations.RunPython.noop),
    ]