from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class WebAuthenticationTests(TestCase):
	def test_register_login_profile_and_logout_flow(self):
		registration = self.client.post(
			reverse('register'),
			{
				'full_name': 'Ada Lovelace',
				'email': 'ada@example.com',
				'phone': '+441234567890',
				'password': 'TailorSensePass123!',
				'password_confirmation': 'TailorSensePass123!',
			},
		)

		self.assertRedirects(registration, reverse('login'))
		self.assertTrue(User.objects.filter(email='ada@example.com').exists())

		login_response = self.client.post(
			reverse('login'),
			{'email': 'ada@example.com', 'password': 'TailorSensePass123!'},
		)

		self.assertRedirects(login_response, reverse('home'))
		home_response = self.client.get(reverse('home'))
		self.assertContains(home_response, 'Ada Lovelace')
		self.assertContains(home_response, 'ada@example.com')
		self.assertContains(home_response, reverse('signout'))

		logout_response = self.client.post(reverse('signout'))
		self.assertRedirects(logout_response, reverse('login'))
		self.assertNotIn('_auth_user_id', self.client.session)

	def test_api_login_route_keeps_distinct_name(self):
		self.assertEqual(reverse('api-login'), '/api/users/login/')
