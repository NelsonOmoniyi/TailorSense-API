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

# Create your tests here.
