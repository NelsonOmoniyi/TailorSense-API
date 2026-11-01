from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .models import Garment, Style


class MeasurementSpecificationValidationTests(TestCase):
    def setUp(self):
        self.garment = Garment.objects.create(name='Validation Garment', slug='validation-garment')
        self.style = Style.objects.create(
            name='Validation Style',
            slug='validation-style',
            garment=self.garment,
        )

    def test_reviewed_specification_requires_source_reviewer_and_date(self):
        self.style.measurement_specification_status = Style.MeasurementSpecificationStatus.REVIEWED

        with self.assertRaises(ValidationError) as raised:
            self.style.full_clean()

        self.assertEqual(
            set(raised.exception.message_dict),
            {
                'measurement_specification_source',
                'measurement_specification_reviewed_by',
                'measurement_specification_reviewed_at',
            },
        )

    def test_validated_specification_requires_practice_validation_provenance(self):
        self.style.measurement_specification_status = Style.MeasurementSpecificationStatus.VALIDATED
        self.style.measurement_specification_source = 'Tailor-approved measurement notes'
        self.style.measurement_specification_reviewed_by = 'Reviewing tailor'
        self.style.measurement_specification_reviewed_at = timezone.now()

        with self.assertRaises(ValidationError) as raised:
            self.style.full_clean()

        self.assertEqual(
            set(raised.exception.message_dict),
            {
                'measurement_specification_validated_by',
                'measurement_specification_validated_at',
            },
        )
