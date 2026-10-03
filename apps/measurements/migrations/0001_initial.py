from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


def seed_measurement_catalog(apps, schema_editor):
    """Create the core types and Kaftan requirements explicitly in the design brief."""
    MeasurementType = apps.get_model('measurements', 'MeasurementType')
    Garment = apps.get_model('measurements', 'Garment')
    Requirement = apps.get_model('measurements', 'GarmentMeasurementRequirement')

    type_rows = [
        ('height', 'Height', 'body', 'Full standing height.'),
        ('neck', 'Neck', 'upper_body', 'Neck circumference.'),
        ('shoulder_width', 'Shoulder Width', 'upper_body', 'Distance across the shoulders.'),
        ('chest', 'Chest', 'upper_body', 'Chest circumference.'),
        ('waist', 'Waist', 'torso', 'Waist circumference.'),
        ('hip_seat', 'Hip/Seat', 'lower_body', 'Circumference around the hips or seat.'),
        ('sleeve_length', 'Sleeve Length', 'upper_body', 'Shoulder-to-wrist sleeve length.'),
        ('shirt_length', 'Shirt Length', 'upper_body', 'Shoulder-to-hem garment length.'),
        ('inseam', 'Inseam', 'lower_body', 'Inside-leg length.'),
    ]
    types_by_code = {}
    for code, name, category, description in type_rows:
        measurement_type, _ = MeasurementType.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'category': category,
                'description': description,
                'is_core': True,
            },
        )
        types_by_code[code] = measurement_type

    kaftan, _ = Garment.objects.get_or_create(
        name="Men's Kaftan",
        defaults={
            'category': 'Traditional',
            'gender': 'men',
            'description': 'Traditional kaftan garment.',
        },
    )
    for code in ('neck', 'shoulder_width', 'chest', 'waist', 'sleeve_length', 'shirt_length'):
        Requirement.objects.get_or_create(
            garment=kaftan,
            measurement_type=types_by_code[code],
            defaults={'is_required': True},
        )


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Garment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('category', models.CharField(max_length=80)),
                ('gender', models.CharField(blank=True, max_length=30)),
                ('description', models.TextField(blank=True)),
            ],
            options={'ordering': ['category', 'name']},
        ),
        migrations.CreateModel(
            name='MeasurementProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('gender', models.CharField(blank=True, max_length=30)),
                ('unit', models.CharField(choices=[('cm', 'Centimeters'), ('in', 'Inches')], default='cm', max_length=2)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='measurement_profiles', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['name', 'id']},
        ),
        migrations.CreateModel(
            name='MeasurementType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('category', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True)),
                ('gender', models.CharField(blank=True, max_length=30)),
                ('is_core', models.BooleanField(default=True)),
            ],
            options={'ordering': ['category', 'name']},
        ),
        migrations.CreateModel(
            name='Measurement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.DecimalField(decimal_places=2, max_digits=7, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('unit', models.CharField(choices=[('cm', 'Centimeters'), ('in', 'Inches')], max_length=2)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('measurement_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='measurements', to='measurements.measurementtype')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='measurements', to='measurements.measurementprofile')),
            ],
            options={'ordering': ['measurement_type__category', 'measurement_type__name']},
        ),
        migrations.CreateModel(
            name='GarmentMeasurementRequirement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_required', models.BooleanField(default=True)),
                ('garment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='measurement_requirements', to='measurements.garment')),
                ('measurement_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='garment_requirements', to='measurements.measurementtype')),
            ],
            options={'ordering': ['garment__name', 'measurement_type__name']},
        ),
        migrations.AddField(
            model_name='garment',
            name='measurement_types',
            field=models.ManyToManyField(blank=True, related_name='garments', through='measurements.GarmentMeasurementRequirement', to='measurements.measurementtype'),
        ),
        migrations.AddConstraint(
            model_name='measurement',
            constraint=models.UniqueConstraint(fields=('profile', 'measurement_type'), name='uniq_measurement_profile_type'),
        ),
        migrations.AddConstraint(
            model_name='measurement',
            constraint=models.CheckConstraint(condition=models.Q(('value__gt', 0)), name='measurement_value_positive'),
        ),
        migrations.AddConstraint(
            model_name='garmentmeasurementrequirement',
            constraint=models.UniqueConstraint(fields=('garment', 'measurement_type'), name='uniq_garment_measurement_requirement'),
        ),
        migrations.RunPython(seed_measurement_catalog, migrations.RunPython.noop),
    ]