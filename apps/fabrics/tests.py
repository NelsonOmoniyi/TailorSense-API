from django.test import TestCase

from .models import Fabric


class FabricRecommendationModelTests(TestCase):
    def test_fabric_model_has_recommendation_fields_only(self):
        field_names = {field.name for field in Fabric._meta.get_fields()}

        required_fields = {
            'name',
            'category',
            'composition',
            'weight_gsm',
            'construction',
            'stretch',
            'drape',
            'structure',
            'breathability',
            'opacity',
        }

        self.assertTrue(required_fields.issubset(field_names))
        self.assertNotIn('color', field_names)
        self.assertNotIn('price_per_meter', field_names)
        self.assertNotIn('stock_units', field_names)
        self.assertNotIn('supplier', field_names)
