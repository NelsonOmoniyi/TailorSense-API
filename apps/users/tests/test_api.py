from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.users.auth import hash_session_key
from apps.users.models import UserProfile


class UserApiTests(TestCase):
    def setUp(self):
        self.registration = {
            'fullname': 'Taylor Example',
            'email': 'taylor@example.com',
            'phone': '1234567890',
            'password': 'tailor-safe-password-123',
            'repeat_password': 'tailor-safe-password-123',
        }

    def test_register_creates_user_and_profile(self):
        response = self.client.post('/api/users/register/', self.registration)

        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(email='taylor@example.com')
        self.assertEqual(user.first_name, 'Taylor Example')
        self.assertEqual(UserProfile.objects.get(user=user).phone, '1234567890')

    def test_register_rejects_duplicate_email(self):
        self.client.post('/api/users/register/', self.registration)

        response = self.client.post('/api/users/register/', self.registration)

        self.assertEqual(response.status_code, 400)

    def test_login_establishes_authenticated_session(self):
        user = get_user_model().objects.create_user(
            username='taylor@example.com',
            email='taylor@example.com',
            password=self.registration['password'],
            first_name='Taylor Example',
        )

        response = self.client.post('/api/users/login/', {
            'email': user.email,
            'password': self.registration['password'],
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['email'], user.email)
        session = self.client.session
        self.assertEqual(session['session_key_hash'], hash_session_key(session.session_key, user.email))

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post('/api/users/login/', {
            'email': 'taylor@example.com',
            'password': 'wrong-password',
        })

        self.assertEqual(response.status_code, 401)

    def test_signout_invalidates_authenticated_session(self):
        user = get_user_model().objects.create_user(
            username='taylor@example.com', email='taylor@example.com', password='safe-password'
        )
        self.client.force_login(user)
        session = self.client.session
        session['session_key_hash'] = hash_session_key(session.session_key, user.email)
        session['user_email'] = user.email
        session['user_phone'] = ''
        session.save()

        response = self.client.post('/api/users/signout/')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)