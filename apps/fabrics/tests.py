from django.test import TestCase

from .models import Fabric


class FabricRecommendationModelTests(TestCase):
    def test_fabric_model_has_recommendation_fields_only(self):
        field_names = {field.name for field in Fabric._meta.get_fields()}

        required_fields = {
            'fabric_name',
            'fiber_category',
            'fiber',
            'fabric_type',
            'composition',
            'construction',
            'weight',
            'stretch',
            'structure',
            'breathability',
            'opacity',
            'created_at',
            'updated_at',
        }

        self.assertTrue(required_fields.issubset(field_names))
        self.assertNotIn('color', field_names)
        self.assertNotIn('price_per_meter', field_names)
        self.assertNotIn('stock_units', field_names)
        self.assertNotIn('supplier', field_names)
