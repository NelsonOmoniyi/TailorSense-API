from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .models import Garment, Style, StyleMeasurementRequirement


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

    def test_agbada_pilot_is_reviewed_with_source_and_resolved_conditions(self):
        style = Style.objects.get(garment__slug='agbada', slug='classic-agbada')
        agbada_styles = Style.objects.filter(garment__slug='agbada', is_active=True)
        requirements = {
            item.measurement_type.code: item
            for item in StyleMeasurementRequirement.objects.filter(style=style).select_related(
                'measurement_type'
            )
        }

        self.assertEqual(
            style.measurement_specification_status,
            Style.MeasurementSpecificationStatus.REVIEWED,
        )
        self.assertEqual(
            style.measurement_specification_reviewed_by,
            'Nelson Omoniyi - Board of Trustees, TairlorSense LTD',
        )
        self.assertEqual(
            style.measurement_specification_reviewed_at.date().isoformat(),
            '2026-11-01',
        )
        self.assertEqual(agbada_styles.count(), 12)
        self.assertTrue(all(
            item.measurement_specification_status == Style.MeasurementSpecificationStatus.REVIEWED
            and item.measurement_requirements.count() == 12
            for item in agbada_styles
        ))
        self.assertIn('User-provided Agbada checklist', style.measurement_specification_source)
        self.assertEqual(len(requirements), 12)
        self.assertTrue(requirements['agbada_length'].is_required)
        self.assertEqual(
            requirements['agbada_length'].notes,
            'Source / Reviewer: Traditional Tailoring Guild Standard',
        )
        self.assertEqual(
            requirements['thigh_circumference'].condition,
            '',
        )
        self.assertEqual(
            requirements['embroidery_area_width'].condition,
            '',
        )
        self.assertEqual(
            requirements['embroidery_area_depth'].condition,
            '',
        )
        self.assertIn('all active Agbada styles include this feature', requirements['thigh_circumference'].notes)
        self.assertIn('all active Agbada styles include this feature', requirements['embroidery_area_width'].notes)
        self.assertFalse(requirements['fila_head_circumference'].is_required)
