from django.db import migrations, models


def add_bubu_measurements(apps, schema_editor):
    """Normalize shared types, then seed Bubu types and code-based requirements."""
    MeasurementType = apps.get_model('measurements', 'MeasurementType')
    Garment = apps.get_model('measurements', 'Garment')
    Requirement = apps.get_model('measurements', 'GarmentMeasurementRequirement')

    # Reuse the original seeded rows so existing foreign keys keep their IDs.
    renamed_types = {
        'neck': ('neck_circumference', 'Neck Circumference', 'upper_body', 'Neck circumference.'),
        'hip_seat': ('full_hip', 'Full Hip', 'hips', 'Circumference around the fullest part of the hips.'),
    }
    for old_code, (new_code, name, category, description) in renamed_types.items():
        old_type = MeasurementType.objects.filter(code=old_code).first()
        canonical_type = MeasurementType.objects.filter(code=new_code).first()
        if old_type and not canonical_type:
            old_type.code = new_code
            old_type.name = name
            old_type.category = category
            old_type.description = description
            old_type.save(update_fields=['code', 'name', 'category', 'description'])

    # is_core describes generally useful profile types; per-garment optionality
    # is represented separately by GarmentMeasurementRequirement.is_required.
    type_rows = [
        ('bust', 'Bust', 'upper_body', 'Circumference around the fullest part of the bust.', 'female', True),
        ('armhole', 'Armhole', 'arms', 'Circumference around the armhole.', 'female', False),
        ('bicep', 'Bicep', 'arms', 'Circumference around the fullest part of the upper arm.', 'female', False),
        ('wrist', 'Wrist', 'arms', 'Circumference around the wrist.', 'female', False),
        ('front_neck_depth', 'Front Neck Depth', 'neckline', 'Vertical measure from the shoulder-neck point to the desired front neckline depth.', 'female', False),
        ('back_neck_depth', 'Back Neck Depth', 'neckline', 'Vertical measure from the shoulder-neck point to the desired back neckline depth.', 'female', False),
        ('dress_length', 'Bubu/Dress Length', 'garment_length', 'Shoulder-to-hem length for the finished gown.', 'female', True),
        ('sleeve_opening', 'Sleeve Opening', 'arms', 'Width or circumference of the sleeve opening, depending on the design.', 'female', False),
    ]
    types_by_code = {}
    for code, name, category, description, gender, is_core in type_rows:
        measurement_type, _ = MeasurementType.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'category': category,
                'description': description,
                'unit': 'cm',
                'gender': gender,
                'is_core': is_core,
            },
        )
        types_by_code[code] = measurement_type

    # Several codes already existed in 0001; resolve them by code, never by ID.
    shared_codes = (
        'height', 'shoulder_width', 'waist', 'full_hip', 'sleeve_length', 'armhole',
        'bicep', 'wrist', 'neck_circumference',
    )
    for code in shared_codes:
        types_by_code[code] = MeasurementType.objects.get(code=code)

    bubu, _ = Garment.objects.get_or_create(
        name="Women's Bubu Gown",
        gender='female',
        defaults={
            'category': 'bubu',
            'description': 'A loose-fitting, flowing gown with a relaxed silhouette and wide or flowing sleeves.',
        },
    )

    required_codes = ('height', 'shoulder_width', 'bust', 'sleeve_length', 'dress_length')
    optional_codes = (
        'waist', 'full_hip', 'armhole', 'bicep', 'wrist', 'neck_circumference',
        'front_neck_depth', 'back_neck_depth', 'sleeve_opening',
    )
    for code in required_codes:
        Requirement.objects.get_or_create(
            garment=bubu,
            measurement_type=types_by_code[code],
            defaults={'is_required': True},
        )
    for code in optional_codes:
        Requirement.objects.get_or_create(
            garment=bubu,
            measurement_type=types_by_code[code],
            defaults={'is_required': False},
        )


class Migration(migrations.Migration):
    dependencies = [
        ('measurements', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='measurementtype',
            name='unit',
            field=models.CharField(
                choices=[('cm', 'Centimeters'), ('in', 'Inches')],
                default='cm',
                max_length=2,
            ),
        ),
        migrations.RunPython(add_bubu_measurements, migrations.RunPython.noop),
    ]