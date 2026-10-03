from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import (
    Garment,
    GarmentMeasurementRequirement,
    Measurement,
    MeasurementProfile,
    MeasurementType,
    StandardMeasurementSet,
)
from apps.users.auth import hash_session_key


class MeasurementSchemaTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='nelson', email='nelson@example.com', password='safe-password'
        )
        self.profile = MeasurementProfile.objects.create(user=self.user, name='Nelson Measurements')
        self.height = MeasurementType.objects.get(code='height')
        self.chest = MeasurementType.objects.get(code='chest')

    def test_profile_stores_measurements_as_individual_rows(self):
        Measurement.objects.create(
            profile=self.profile,
            measurement_type=self.height,
            value=Decimal('178.00'),
            unit='cm',
        )
        Measurement.objects.create(
            profile=self.profile,
            measurement_type=self.chest,
            value=Decimal('102.00'),
            unit='cm',
        )

        self.assertEqual(self.profile.measurements.count(), 2)
        self.assertEqual(self.profile.measurements.get(measurement_type=self.height).value, Decimal('178.00'))

    def test_profile_cannot_store_duplicate_measurement_type(self):
        Measurement.objects.create(
            profile=self.profile,
            measurement_type=self.height,
            value=Decimal('178.00'),
            unit='cm',
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Measurement.objects.create(
                profile=self.profile,
                measurement_type=self.height,
                value=Decimal('179.00'),
                unit='cm',
            )

    def test_same_measurement_type_can_be_saved_for_another_profile(self):
        other_profile = MeasurementProfile.objects.create(user=self.user, name='Summer Measurements')

        first = Measurement.objects.create(
            profile=self.profile,
            measurement_type=self.height,
            value=Decimal('178.00'),
            unit='cm',
        )
        second = Measurement.objects.create(
            profile=other_profile,
            measurement_type=self.height,
            value=Decimal('180.00'),
            unit='cm',
        )

        self.assertNotEqual(first.value, second.value)

    def test_garment_requirements_are_unique_per_type(self):
        garment = Garment.objects.create(name="Men's Kaftan", category='Traditional', gender='men')
        requirement = GarmentMeasurementRequirement.objects.create(
            garment=garment,
            measurement_type=self.chest,
        )

        self.assertIn(self.chest, garment.measurement_types.all())
        with self.assertRaises(IntegrityError), transaction.atomic():
            GarmentMeasurementRequirement.objects.create(
                garment=garment,
                measurement_type=self.chest,
            )

    def test_seeded_garments_have_their_measurement_requirements(self):
        kaftan = Garment.objects.get(name="Men's Kaftan")
        kaftan_requirements = dict(
            kaftan.measurement_requirements.values_list('measurement_type__code', 'is_required')
        )
        self.assertEqual(
            {code for code, required in kaftan_requirements.items() if required},
            {'neck_circumference', 'shoulder_width', 'chest', 'waist', 'sleeve_length', 'shirt_length'},
        )

        bubu = Garment.objects.get(name="Women's Bubu Gown")
        bubu_requirements = dict(
            bubu.measurement_requirements.values_list('measurement_type__code', 'is_required')
        )
        self.assertEqual(
            {code for code, required in bubu_requirements.items() if required},
            {'height', 'shoulder_width', 'bust', 'sleeve_length', 'dress_length'},
        )
        self.assertEqual(
            {code for code, required in bubu_requirements.items() if not required},
            {
                'waist', 'full_hip', 'armhole', 'bicep', 'wrist',
                'neck_circumference', 'front_neck_depth', 'back_neck_depth', 'sleeve_opening',
            },
        )

    def test_measurement_types_have_a_default_unit(self):
        self.assertEqual(self.height.unit, 'cm')
        self.assertEqual(MeasurementType.objects.filter(code='hip_seat').count(), 0)
        self.assertEqual(MeasurementType.objects.filter(code='full_hip').count(), 1)


class MeasurementApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='api-user', email='api-user@example.com', password='safe-password'
        )
        self.client.force_login(self.user)
        session = self.client.session
        session['session_key_hash'] = hash_session_key(session.session_key, self.user.email)
        session['user_email'] = self.user.email
        session['user_phone'] = ''
        session.save()
        self.payload = {
            'name': 'Everyday Measurements',
            'gender': 'female',
            'unit': 'cm',
            'measurements': [
                {'measurement_type': 'height', 'value': '165'},
                {'measurement_type': 'bust', 'value': '94'},
                {'measurement_type': 'dress_length', 'value': '140'},
            ],
        }

    def test_measurement_type_api_returns_seeded_catalog(self):
        response = self.client.get('/api/measurements/types/')

        self.assertEqual(response.status_code, 200)
        types_by_code = {item['code']: item for item in response.json()}
        self.assertEqual(types_by_code['bust']['gender'], 'female')
        self.assertEqual(types_by_code['height']['unit'], 'cm')

    def test_profile_api_creates_profile_and_measurement_rows(self):
        response = self.client.post(
            '/api/measurements/profiles/',
            self.payload,
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        profile = MeasurementProfile.objects.get(user=self.user, name='Everyday Measurements')
        self.assertEqual(profile.measurements.count(), 3)
        self.assertEqual(response.json()['measurements'][0]['measurement_type']['code'], 'height')

    def test_profile_api_lists_only_the_signed_in_users_profiles(self):
        MeasurementProfile.objects.create(user=self.user, name='My Profile')
        another_user = get_user_model().objects.create_user(
            username='another-user', email='another@example.com', password='safe-password'
        )
        MeasurementProfile.objects.create(user=another_user, name='Private Profile')

        response = self.client.get('/api/measurements/profiles/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['name'] for item in response.json()], ['My Profile'])

    def test_standard_sets_are_shared_and_include_field_requirements(self):
        response = self.client.get('/api/measurements/standards/')

        self.assertEqual(response.status_code, 200)
        standards = response.json()
        self.assertEqual(len(standards), 4)
        self.assertEqual(MeasurementProfile.objects.count(), 0)
        male_casual = next(item for item in standards if item['gender'] == 'male' and item['context'] == 'casual')
        required_codes = {
            item['measurement_type']['code']
            for item in male_casual['requirements']
            if item['is_required']
        }
        self.assertIn('height', required_codes)
        self.assertIn('weight', required_codes)

    def test_weight_type_and_saved_value_use_mass_units(self):
        weight_type = MeasurementType.objects.get(code='weight')
        response = self.client.post(
            '/api/measurements/profiles/',
            {
                **self.payload,
                'measurements': [{'measurement_type': 'weight', 'value': '68'}],
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        measurement = Measurement.objects.get(measurement_type=weight_type)
        self.assertEqual(measurement.unit, 'kg')

    def test_profile_api_rejects_duplicate_measurement_types(self):
        payload = {
            **self.payload,
            'measurements': [
                {'measurement_type': 'height', 'value': '165'},
                {'measurement_type': 'height', 'value': '166'},
            ],
        }

        response = self.client.post(
            '/api/measurements/profiles/',
            payload,
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(MeasurementProfile.objects.filter(user=self.user).exists())