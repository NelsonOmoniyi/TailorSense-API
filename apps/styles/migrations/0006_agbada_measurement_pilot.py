"""Seed the user-supplied Agbada measurement checklist as unreviewed draft data."""

from django.db import migrations


MEASUREMENTS = [
    {
        'code': 'agbada_length',
        'name': 'Agbada Length',
        'category': 'garment_length',
        'description': 'Measure from the nape of the neck down to the preferred length.',
        'required': True,
        'instructions': (
            'Measure from the nape of the neck (center back) down to the ankles or preferred '
            'length, usually mid-calf to ankle.'
        ),
        'source': 'Traditional Tailoring Guild Standard',
    },
    {
        'code': 'agbada_span',
        'name': 'Agbada Width (Span)',
        'category': 'upper_body',
        'description': 'Measure the wrist-to-wrist span with arms extended.',
        'required': True,
        'instructions': 'Measure from wrist to wrist with arms fully extended horizontally.',
        'source': 'Traditional Tailoring Guild Standard',
    },
    {
        'code': 'neck_circumference',
        'name': 'Neck Circumference',
        'category': 'upper_body',
        'description': 'Measure around the base of the neck.',
        'required': True,
        'instructions': (
            'Measure around the base of the neck where the collar sits, leaving room for two '
            'fingers for comfort.'
        ),
        'source': 'Traditional Tailoring Guild Standard',
    },
    {
        'code': 'buba_length',
        'name': 'Inner Tunic (Buba) Length',
        'category': 'garment_length',
        'description': 'Measure the length of the inner tunic.',
        'required': True,
        'instructions': 'Measure from the shoulder line to just below the hip or mid-thigh.',
        'source': 'Master Tailor Review Board',
    },
    {
        'code': 'buba_sleeve_length',
        'name': 'Inner Tunic Sleeve Length',
        'category': 'upper_body',
        'description': 'Measure the sleeve length of the inner tunic.',
        'required': True,
        'instructions': 'Measure from the shoulder tip down to the wrist bone.',
        'source': 'Master Tailor Review Board',
    },
    {
        'code': 'chest',
        'name': 'Chest / Bust',
        'category': 'upper_body',
        'description': 'Measure around the fullest part of the chest.',
        'required': True,
        'instructions': (
            'Measure around the fullest part of the chest, keeping the tape horizontal and relaxed.'
        ),
        'source': 'Standard Garment Specification',
    },
    {
        'code': 'trouser_length',
        'name': 'Trouser (Sokoto) Length',
        'category': 'garment_length',
        'description': 'Measure the outside-seam length of the Sokoto trousers.',
        'required': True,
        'instructions': (
            'Measure from the waistline down to the ankle bone along the outside seam.'
        ),
        'source': 'Standard Garment Specification',
    },
    {
        'code': 'waist',
        'name': 'Waist',
        'category': 'torso',
        'description': 'Measure around the natural waistline.',
        'required': True,
        'instructions': (
            'Measure around the natural waistline where the Sokoto trousers will be tied or fastened.'
        ),
        'source': 'Standard Garment Specification',
    },
    {
        'code': 'thigh_circumference',
        'name': 'Thigh Circumference',
        'category': 'lower_body',
        'description': 'Measure around the widest part of the upper thigh.',
        'required': True,
        'condition': 'Only if the style includes Sokoto Kembe (three-quarter, loose).',
        'instructions': (
            'Measure around the widest part of the upper thigh to ensure a traditional loose fit.'
        ),
        'source': 'Traditional Tailoring Guild Standard',
    },
    {
        'code': 'fila_head_circumference',
        'name': 'Cap Size (Fila)',
        'category': 'headwear',
        'description': 'Measure the head circumference for a Fila cap.',
        'required': False,
        'instructions': 'Measure just above the ears and eyebrows.',
        'source': 'Embroidery & Accessories Guild',
    },
    {
        'code': 'embroidery_area_width',
        'name': 'Embroidery Area Width',
        'category': 'garment_detail',
        'description': 'Measure the width of the chest-panel embroidery area.',
        'required': True,
        'condition': 'Only if the style includes custom chest embroidery.',
        'instructions': 'Measure the width across the chest panel.',
        'source': 'Master Embroidery Review',
    },
    {
        'code': 'embroidery_area_depth',
        'name': 'Embroidery Area Depth',
        'category': 'garment_detail',
        'description': 'Measure the depth of the chest-panel embroidery area.',
        'required': True,
        'condition': 'Only if the style includes custom chest embroidery.',
        'instructions': 'Measure from the collar down to the required embroidery boundary.',
        'source': 'Master Embroidery Review',
    },
]


def seed_agbada_measurements(apps, schema_editor):
    database = schema_editor.connection.alias
    Garment = apps.get_model('styles', 'Garment')
    Style = apps.get_model('styles', 'Style')
    Requirement = apps.get_model('styles', 'StyleMeasurementRequirement')
    MeasurementType = apps.get_model('measurements', 'MeasurementType')

    garment = Garment.objects.using(database).filter(slug='agbada').first()
    if garment is None:
        return

    measurement_types = {}
    for item in MEASUREMENTS:
        measurement_type, _ = MeasurementType.objects.using(database).get_or_create(
            code=item['code'],
            defaults={
                'name': item['name'],
                'category': item['category'],
                'description': item['description'],
                'unit': 'cm',
                'gender': 'male',
                'is_core': item['required'],
            },
        )
        measurement_types[item['code']] = measurement_type

    styles = Style.objects.using(database).filter(garment=garment, is_active=True)
    for style in styles:
        style.measurement_specification_status = 'draft'
        if not style.measurement_specification_source:
            style.measurement_specification_source = (
                'User-supplied Agbada checklist; see each requirement note for its source.'
            )
        style.save(
            using=database,
            update_fields=[
                'measurement_specification_status',
                'measurement_specification_source',
            ],
        )
        for display_order, item in enumerate(MEASUREMENTS):
            Requirement.objects.using(database).get_or_create(
                style=style,
                measurement_type=measurement_types[item['code']],
                defaults={
                    'is_required': item['required'],
                    'purpose': 'recommendation',
                    'instructions': item['instructions'],
                    'condition': item.get('condition', ''),
                    'notes': f"Source / Reviewer: {item['source']}",
                    'display_order': display_order,
                },
            )


class Migration(migrations.Migration):

    dependencies = [
        ('measurements', '0007_alter_measurement_unit_alter_measurementtype_unit'),
        ('styles', '0005_style_measurement_specification_reviewed_at_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_agbada_measurements, migrations.RunPython.noop),
    ]
