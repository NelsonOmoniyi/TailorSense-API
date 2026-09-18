from django.test import TestCase

from apps.fabrics.models import Fabric


class FabricModelTest(TestCase):
    def test_create_fabric(self):
        fabric = Fabric.objects.create(
            name='Cotton Twill',
            category='Cotton',
            composition='100% Cotton',
            color='Navy',
            weight_gsm=220,
            price_per_meter=12.50,
            stock_units=25,
            supplier='Local Mill',
        )

        self.assertEqual(fabric.name, 'Cotton Twill')
        self.assertEqual(fabric.category, 'Cotton')
        self.assertTrue(str(fabric).startswith('Cotton Twill'))
