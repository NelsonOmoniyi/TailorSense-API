from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from django.utils import timezone

from apps.fabrics.models import Fabric
from apps.measurements.models import Measurement, MeasurementProfile, MeasurementType
from apps.styles.models import (
    Garment,
    Occasion,
    Style,
    StyleFabric,
    StyleImage,
    StyleMeasurementRequirement,
)


class RecommendationsApiTests(APITestCase):
    endpoint = '/api/v1/recommendations/'

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='recommendation-user',
            email='recommendation@example.com',
            password='safe-password',
        )
        self.client.force_authenticate(user=self.user, token='test-jwt')
        self.profile = MeasurementProfile.objects.create(
            user=self.user,
            name='Everyday',
            gender='female',
            unit='cm',
        )
        self.bust, _ = MeasurementType.objects.get_or_create(
            code='bust',
            defaults={'name': 'Bust', 'category': 'upper_body'},
        )
        Measurement.objects.create(
            profile=self.profile,
            measurement_type=self.bust,
            value='92.00',
            unit='cm',
        )
        self.garment, _ = Garment.objects.get_or_create(
            slug='recommendation-test-gowns',
            defaults={'name': 'Recommendation Test Gowns', 'is_active': True},
        )
        self.fabric = Fabric.objects.create(fabric_name='Recommendation Test Cotton')
        self.occasion, _ = Occasion.objects.get_or_create(name='Casual')
        self.style = self.make_style(
            'Everyday Gown',
            'everyday-gown',
            measurement_specification_status=Style.MeasurementSpecificationStatus.REVIEWED,
        )
        self.link_style(self.style, StyleFabric.Suitability.EXCELLENT)
        StyleMeasurementRequirement.objects.create(
            style=self.style,
            measurement_type=self.bust,
            is_required=True,
        )
        self.style.occasions.add(self.occasion)

    def make_style(
        self,
        name,
        slug,
        *,
        gender='female',
        active=True,
        measurement_specification_status=Style.MeasurementSpecificationStatus.NOT_CONFIGURED,
    ):
        review_fields = {}
        if measurement_specification_status in {
            Style.MeasurementSpecificationStatus.REVIEWED,
            Style.MeasurementSpecificationStatus.VALIDATED,
        }:
            review_fields.update({
                'measurement_specification_source': 'Tailor-reviewed test checklist',
                'measurement_specification_reviewed_by': 'Test tailor',
                'measurement_specification_reviewed_at': timezone.now(),
            })
        if measurement_specification_status == Style.MeasurementSpecificationStatus.VALIDATED:
            review_fields.update({
                'measurement_specification_validated_by': 'Test validator',
                'measurement_specification_validated_at': timezone.now(),
            })
        return Style.objects.create(
            name=name,
            slug=slug,
            garment=self.garment,
            gender=gender,
            is_active=active,
            measurement_specification_status=measurement_specification_status,
            **review_fields,
        )

    def link_style(self, style, suitability, *, active=True, fabric=None):
        return StyleFabric.objects.create(
            style=style,
            fabric=fabric or self.fabric,
            suitability=suitability,
            is_active=active,
        )

    def request_data(self, **overrides):
        data = {
            'measurement_profile_id': self.profile.pk,
            'fabric_id': self.fabric.pk,
            'category': self.garment.slug,
        }
        data.update(overrides)
        return data

    def test_returns_ranked_recommendations_with_images_and_evidence(self):
        second_style = self.make_style('Relaxed Gown', 'relaxed-gown')
        self.link_style(second_style, StyleFabric.Suitability.GOOD)
        StyleMeasurementRequirement.objects.create(
            style=second_style,
            measurement_type=self.bust,
            is_required=True,
        )
        StyleImage.objects.create(
            style=self.style,
            image='styles/secondary.jpg',
            display_order=0,
        )
        StyleImage.objects.create(
            style=self.style,
            image='styles/primary.jpg',
            display_order=1,
            is_primary=True,
        )

        response = self.client.post(
            self.endpoint,
            self.request_data(occasion='casual'),
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['category'], self.garment.slug)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['style_id'], self.style.pk)
        self.assertEqual(response.data['results'][0]['score'], 100.0)
        self.assertEqual(len(response.data['results'][0]['images']), 2)
        self.assertIn('/media/styles/primary.jpg', response.data['results'][0]['images'][0]['image'])
        self.assertTrue(response.data['results'][0]['images'][0]['is_primary'])
        self.assertTrue(any('fabric suitability' in reason for reason in response.data['results'][0]['reasons']))
        result_ids = [item['style_id'] for item in response.data['results']]
        self.assertEqual(len(result_ids), len(set(result_ids)))
        self.assertEqual(response.data['missing_measurements'], [])

        repeated_response = self.client.post(
            self.endpoint,
            self.request_data(occasion='casual'),
            format='json',
        )
        self.assertEqual(
            [item['style_id'] for item in repeated_response.data['results']],
            result_ids,
        )

    def test_excludes_inactive_mismatched_unsuitable_and_incomplete_styles(self):
        inactive = self.make_style('Inactive Gown', 'inactive-gown', active=False)
        self.link_style(inactive, StyleFabric.Suitability.GOOD)
        wrong_gender = self.make_style('Men Gown', 'men-gown', gender='male')
        self.link_style(wrong_gender, StyleFabric.Suitability.EXCELLENT)
        unsuitable = self.make_style('Unsuitable Gown', 'unsuitable-gown')
        self.link_style(unsuitable, StyleFabric.Suitability.UNSUITABLE)
        inactive_link = self.make_style('Inactive Link Gown', 'inactive-link-gown')
        self.link_style(inactive_link, StyleFabric.Suitability.GOOD, active=False)
        incomplete = self.make_style(
            'Incomplete Gown',
            'incomplete-gown',
            measurement_specification_status=Style.MeasurementSpecificationStatus.REVIEWED,
        )
        self.link_style(incomplete, StyleFabric.Suitability.EXCELLENT)
        waist, _ = MeasurementType.objects.get_or_create(
            code='waist',
            defaults={'name': 'Waist', 'category': 'torso'},
        )
        StyleMeasurementRequirement.objects.create(
            style=incomplete,
            measurement_type=waist,
            is_required=True,
        )

        response = self.client.post(self.endpoint, self.request_data(), format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item['style_id'] for item in response.data['results']],
            [self.style.pk],
        )
        self.assertEqual(
            response.data['missing_measurements'],
            [{'code': 'waist', 'name': 'Waist'}],
        )
        self.assertEqual(
            response.data['excluded_for_measurements'],
            [{
                'style_id': incomplete.pk,
                'name': incomplete.name,
                'measurement_check': {
                    'status': 'incomplete',
                    'specification_status': Style.MeasurementSpecificationStatus.REVIEWED,
                    'missing_measurements': [{'code': 'waist', 'name': 'Waist'}],
                },
                'missing_measurements': [{'code': 'waist', 'name': 'Waist'}],
            }],
        )

    def test_rejects_unauthenticated_and_foreign_profiles(self):
        self.client.force_authenticate(user=None)
        unauthenticated = self.client.post(self.endpoint, self.request_data(), format='json')
        self.assertEqual(unauthenticated.status_code, 403)

        other_user = get_user_model().objects.create_user(
            username='other-user',
            email='other@example.com',
            password='safe-password',
        )
        foreign_profile = MeasurementProfile.objects.create(
            user=other_user,
            name='Private profile',
            gender='female',
        )
        self.client.force_authenticate(user=self.user, token='test-jwt')
        response = self.client.post(
            self.endpoint,
            self.request_data(measurement_profile_id=foreign_profile.pk),
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('measurement_profile_id', response.data)

    def test_validates_fabric_category_occasion_limit_and_unsupported_fields(self):
        invalid_requests = [
            ({'measurement_profile_id': 999999}, 'measurement_profile_id'),
            ({'fabric_id': 999999}, 'fabric_id'),
            ({'category': 'not-a-category'}, 'category'),
            ({'occasion': 'not-recorded'}, 'occasion'),
            ({'limit': 21}, 'limit'),
            ({'preferences': {'fit_type': 'relaxed'}}, 'preferences'),
        ]
        for overrides, field in invalid_requests:
            with self.subTest(field=field):
                response = self.client.post(
                    self.endpoint,
                    self.request_data(**overrides),
                    format='json',
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)

    def test_returns_empty_results_when_no_fabric_link_exists(self):
        other_fabric = Fabric.objects.create(fabric_name='Recommendation Test Linen')

        response = self.client.post(
            self.endpoint,
            self.request_data(fabric_id=other_fabric.pk),
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['missing_measurements'], [])

    def test_styles_without_images_are_returned_with_empty_image_lists(self):
        response = self.client.post(self.endpoint, self.request_data(), format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['images'], [])

    def test_missing_optional_measurement_keeps_style_eligible_and_reduces_score(self):
        waist, _ = MeasurementType.objects.get_or_create(
            code='waist',
            defaults={'name': 'Waist', 'category': 'torso'},
        )
        StyleMeasurementRequirement.objects.create(
            style=self.style,
            measurement_type=waist,
            is_required=False,
        )

        response = self.client.post(self.endpoint, self.request_data(), format='json')

        self.assertEqual(response.status_code, 200)
        result = response.data['results'][0]
        self.assertEqual(result['style_id'], self.style.pk)
        self.assertEqual(result['score'], 78.6)
        self.assertEqual(result['missing_measurements'], [{'code': 'waist', 'name': 'Waist'}])
        self.assertEqual(response.data['missing_measurements'], [])
        self.assertEqual(result['measurement_check']['status'], 'optional_missing')

    def test_unreviewed_checklists_are_unknown_and_do_not_gate_or_score(self):
        draft = self.make_style(
            'Draft Checklist Gown',
            'draft-checklist-gown',
            measurement_specification_status=Style.MeasurementSpecificationStatus.DRAFT,
        )
        self.link_style(draft, StyleFabric.Suitability.EXCELLENT)
        waist, _ = MeasurementType.objects.get_or_create(
            code='waist',
            defaults={'name': 'Waist', 'category': 'torso'},
        )
        StyleMeasurementRequirement.objects.create(style=draft, measurement_type=waist)
        unconfigured = self.make_style('Unconfigured Gown', 'unconfigured-gown')
        self.link_style(unconfigured, StyleFabric.Suitability.GOOD)

        response = self.client.post(self.endpoint, self.request_data(), format='json')

        self.assertEqual(response.status_code, 200)
        results = {item['style_id']: item for item in response.data['results']}
        self.assertIn(draft.pk, results)
        self.assertEqual(results[draft.pk]['measurement_check']['status'], 'draft')
        self.assertEqual(results[draft.pk]['score'], 100.0)
        self.assertEqual(
            results[unconfigured.pk]['measurement_check']['status'],
            'not_configured',
        )
        self.assertEqual(response.data['excluded_for_measurements'], [])

    def test_drafting_only_measurements_do_not_affect_recommendation_completeness(self):
        drafting_style = self.make_style(
            'Drafting Only Gown',
            'drafting-only-gown',
            measurement_specification_status=Style.MeasurementSpecificationStatus.REVIEWED,
        )
        self.link_style(drafting_style, StyleFabric.Suitability.EXCELLENT)
        waist, _ = MeasurementType.objects.get_or_create(
            code='waist',
            defaults={'name': 'Waist', 'category': 'torso'},
        )
        StyleMeasurementRequirement.objects.create(
            style=drafting_style,
            measurement_type=waist,
            purpose=StyleMeasurementRequirement.Purpose.DRAFTING,
        )

        response = self.client.post(self.endpoint, self.request_data(), format='json')

        result = next(
            item for item in response.data['results'] if item['style_id'] == drafting_style.pk
        )
        self.assertEqual(result['measurement_check']['status'], 'no_recommendation_requirements')
        self.assertEqual(result['missing_measurements'], [])
        self.assertEqual(result['score'], 100.0)

    def test_conditional_requirements_are_returned_without_automatic_evaluation(self):
        waist, _ = MeasurementType.objects.get_or_create(
            code='waist',
            defaults={'name': 'Waist', 'category': 'torso'},
        )
        StyleMeasurementRequirement.objects.create(
            style=self.style,
            measurement_type=waist,
            condition='Only if the selected design includes a fitted waist.',
        )

        response = self.client.post(self.endpoint, self.request_data(), format='json')

        result = response.data['results'][0]
        self.assertEqual(result['measurement_check']['status'], 'conditional_unresolved')
        self.assertEqual(
            result['measurement_check']['conditional_requirements'],
            [{
                'code': 'waist',
                'name': 'Waist',
                'condition': 'Only if the selected design includes a fitted waist.',
            }],
        )
        self.assertTrue(any('not evaluated automatically' in reason for reason in result['reasons']))

    def test_fabric_compatibility_evidence_includes_suitability_and_notes(self):
        link = self.style.fabric_links.get()
        link.notes = 'Suitable for a lightweight finish.'
        link.save(update_fields=['notes'])

        response = self.client.post(self.endpoint, self.request_data(), format='json')

        compatibility = response.data['results'][0]['fabric_compatibility']
        self.assertEqual(compatibility['suitability'], StyleFabric.Suitability.EXCELLENT)
        self.assertEqual(compatibility['notes'], 'Suitable for a lightweight finish.')

    def test_validated_specification_is_identified_in_measurement_check(self):
        validated = self.make_style(
            'Validated Gown',
            'validated-gown',
            measurement_specification_status=Style.MeasurementSpecificationStatus.VALIDATED,
        )
        self.link_style(validated, StyleFabric.Suitability.GOOD)
        StyleMeasurementRequirement.objects.create(
            style=validated,
            measurement_type=self.bust,
        )

        response = self.client.post(self.endpoint, self.request_data(), format='json')

        result = next(
            item for item in response.data['results'] if item['style_id'] == validated.pk
        )
        self.assertEqual(result['measurement_check']['status'], 'complete')
        self.assertEqual(
            result['measurement_check']['specification_status'],
            Style.MeasurementSpecificationStatus.VALIDATED,
        )

    def test_style_api_cannot_change_measurement_review_status(self):
        response = self.client.patch(
            f'/api/v1/styles/{self.style.pk}/',
            {'measurement_specification_status': Style.MeasurementSpecificationStatus.VALIDATED},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.style.refresh_from_db()
        self.assertEqual(
            self.style.measurement_specification_status,
            Style.MeasurementSpecificationStatus.REVIEWED,
        )
