from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.users.auth import hash_session_key


class AddFabricViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='catalogue-editor', email='editor@example.com', password='safe-password'
        )
        self.client.force_login(self.user)
        session = self.client.session
        session['session_key_hash'] = hash_session_key(session.session_key, self.user.email)
        session['user_email'] = self.user.email
        session['user_phone'] = ''
        session.save()

    @patch('apps.core.views.requests.post')
    def test_add_fabric_relays_form_to_fabrics_api(self, mock_post):
        mock_post.return_value = SimpleNamespace(status_code=201)

        response = self.client.post('/fabrics/add/', {'fabric_name': 'Linen'})

        self.assertRedirects(response, '/fabrics/')
        mock_post.assert_called_once()
        self.assertEqual(mock_post.call_args.kwargs['data']['fabric_name'], 'Linen')


class CoreAccountFlowTests(TestCase):
    @patch('apps.core.views.requests.post')
    def test_register_page_delegates_to_user_api(self, mock_post):
        mock_post.return_value = SimpleNamespace(status_code=201, cookies={})

        response = self.client.post('/register/', {
            'fullname': 'Taylor Example',
            'email': 'taylor@example.com',
            'phone': '1234567890',
            'password': 'tailor-safe-password-123',
            'repeat_password': 'tailor-safe-password-123',
        })

        self.assertRedirects(response, '/login/')
        self.assertTrue(mock_post.call_args.args[0].endswith('/api/users/register/'))

    @patch('apps.core.views.requests.post')
    def test_login_page_delegates_to_user_api_and_relays_session_cookie(self, mock_post):
        mock_post.return_value = SimpleNamespace(
            status_code=200,
            cookies={'sessionid': 'api-session', 'csrftoken': 'api-csrf'},
        )

        response = self.client.post('/login/', {
            'email': 'taylor@example.com',
            'password': 'safe-password',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/home/')
        self.assertEqual(response.cookies['sessionid'].value, 'api-session')
        self.assertTrue(mock_post.call_args.args[0].endswith('/api/users/login/'))

    @patch('apps.core.views.requests.post')
    def test_signout_delegates_to_user_api_and_clears_local_session(self, mock_post):
        user = get_user_model().objects.create_user(
            username='catalogue-editor', email='editor@example.com', password='safe-password'
        )
        self.client.force_login(user)
        session = self.client.session
        session['session_key_hash'] = hash_session_key(session.session_key, user.email)
        session['user_email'] = user.email
        session['user_phone'] = ''
        session.save()
        mock_post.return_value = SimpleNamespace(status_code=200, cookies={})

        response = self.client.post('/signout/')

        self.assertRedirects(response, '/')
        self.assertTrue(mock_post.call_args.args[0].endswith('/api/users/signout/'))
        self.assertNotIn('_auth_user_id', self.client.session)

# Create your tests here.
