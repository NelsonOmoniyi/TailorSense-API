from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.users.auth import hash_session_key
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


class FabricApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='fabric-admin', email='admin@example.com', password='safe-password'
        )
        self.client.force_login(self.user)
        session = self.client.session
        session['session_key_hash'] = hash_session_key(session.session_key, self.user.email)
        session['user_email'] = self.user.email
        session['user_phone'] = ''
        session.save()
        self.payload = {
            'fabric_name': 'Cotton Poplin',
            'fiber_category': 'Natural',
            'fiber': 'Cotton',
            'fabric_type': 'Poplin',
            'composition': '100% cotton',
            'construction': 'Woven',
            'weight': '120 gsm',
            'stretch': 'none',
            'structure': 'Plain weave',
            'breathability': 'high',
            'opacity': 'medium',
        }

    def test_add_fabric_api_creates_and_returns_fabric(self):
        response = self.client.post('/api/fabrics/add/', self.payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['fabric_name'], 'Cotton Poplin')
        self.assertTrue(Fabric.objects.filter(fabric_name='Cotton Poplin').exists())

    def test_add_fabric_api_rejects_invalid_property_level(self):
        response = self.client.post('/api/fabrics/add/', {**self.payload, 'stretch': 'very-high'})

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Fabric.objects.exists())
