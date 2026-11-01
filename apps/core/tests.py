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


class HomeSectionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='workspace-user', email='workspace@example.com', password='safe-password'
        )
        self.client.force_login(self.user)
        session = self.client.session
        session['session_key_hash'] = hash_session_key(session.session_key, self.user.email)
        session['user_email'] = self.user.email
        session['user_phone'] = ''
        session.save()

    @patch('apps.core.views.requests.get')
    def test_reference_sections_render_inside_shared_workspace_shell(self, mock_get):
        def measurement_api_response(url, **kwargs):
            if url.endswith('/types/'):
                return SimpleNamespace(status_code=200, ok=True, json=lambda: [
                    {'name': 'Height', 'code': 'height', 'category': 'body', 'unit': 'cm', 'is_core': True},
                ])
            return SimpleNamespace(status_code=200, ok=True, json=lambda: [])

        mock_get.side_effect = measurement_api_response
        pages = [
            ('/profile/', 'Profile information', 'home.html'),
            ('/measurements/', 'No measurement profiles yet', 'measurements/dashboard.html'),
            ('/styles/', 'No styles to show yet', 'styles/dashboard.html'),
            ('/recommendations/', 'No measurement profiles yet', 'recommendations/dashboard.html'),
            ('/orders/', 'No orders yet', 'home.html'),
            ('/settings/', 'Notifications', 'home.html'),
        ]

        for path, expected_content, expected_template in pages:
            with self.subTest(path=path):
                response = self.client.get(path)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'workspace-sidebar')
                self.assertContains(response, 'workspace-topbar')
                self.assertContains(response, expected_content)
                self.assertTemplateUsed(response, expected_template)

    @patch('apps.core.views.requests.get')
    def test_dashboard_uses_shared_shell_and_real_fabric_count(self, mock_get):
        mock_get.return_value = SimpleNamespace(
            status_code=200,
            json=lambda: [{'fabric_name': 'Cotton Poplin', 'fiber_category': 'Natural'}],
        )

        response = self.client.get('/home/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<title>Home | TailorSense</title>', html=False)
        self.assertContains(response, 'workspace-sidebar')
        self.assertContains(response, 'Cotton Poplin')
        self.assertContains(response, '>1</strong>')


class MeasurementsDashboardProxyTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='measurement-user', email='measurement@example.com', password='safe-password'
        )
        self.client.force_login(self.user)
        session = self.client.session
        session['session_key_hash'] = hash_session_key(session.session_key, self.user.email)
        session['user_email'] = self.user.email
        session['user_phone'] = ''
        session.save()

    @patch('apps.core.views.requests.get')
    def test_measurements_dashboard_renders_profiles_returned_by_api(self, mock_get):
        def api_response(url, **kwargs):
            if url.endswith('/types/'):
                return SimpleNamespace(status_code=200, json=lambda: [
                    {'name': 'Height', 'code': 'height', 'category': 'body', 'unit': 'cm', 'is_core': True},
                ])
            return SimpleNamespace(status_code=200, json=lambda: [{
                'id': 1,
                'name': 'Everyday Measurements',
                'gender': 'female',
                'unit': 'cm',
                'measurements': [{
                    'measurement_type': {'name': 'Height', 'code': 'height'},
                    'value': '165.00',
                    'unit': 'cm',
                }],
            }])

        mock_get.side_effect = api_response

        response = self.client.get('/measurements/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Everyday Measurements')
        self.assertContains(response, '165.00')
        self.assertContains(response, 'Height')
        self.assertEqual(mock_get.call_count, 2)

    @patch('apps.core.views.requests.post')
    def test_measurement_form_relays_profile_and_nonblank_rows_to_api(self, mock_post):
        mock_post.return_value = SimpleNamespace(status_code=201)

        response = self.client.post('/measurements/add/', {
            'name': 'Everyday Measurements',
            'gender': 'female',
            'unit': 'cm',
            'measurement_type_code': ['height', 'bust', 'waist'],
            'measurement_value': ['165', '94', ''],
        })

        self.assertRedirects(response, '/measurements/')
        self.assertEqual(
            mock_post.call_args.kwargs['json']['measurements'],
            [
                {'measurement_type': 'height', 'value': '165', 'unit': 'cm'},
                {'measurement_type': 'bust', 'value': '94', 'unit': 'cm'},
            ],
        )


class RecommendationsDashboardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='recommendation-ui-user',
            email='recommendation-ui@example.com',
            password='safe-password',
        )
        self.client.force_login(self.user)
        session = self.client.session
        session['session_key_hash'] = hash_session_key(session.session_key, self.user.email)
        session['user_email'] = self.user.email
        session['user_phone'] = ''
        session.save()

    @patch('apps.core.views.requests.post')
    @patch('apps.core.views.requests.get')
    def test_dashboard_submits_recommendation_request_to_api(self, mock_get, mock_post):
        def option_response(url, **kwargs):
            if url.endswith('/profiles/'):
                data = [{'id': 12, 'name': 'Everyday', 'gender': 'female'}]
            elif url.endswith('/list/'):
                data = [{'id': 7, 'fabric_name': 'Cotton'}]
            else:
                data = [{'id': 4, 'name': 'Gowns', 'slug': 'gowns'}]
            return SimpleNamespace(status_code=200, json=lambda: data)

        mock_get.side_effect = option_response
        mock_post.return_value = SimpleNamespace(
            status_code=200,
            json=lambda: {
                'category': 'gowns',
                'count': 1,
                'missing_measurements': [],
                'results': [{
                    'name': 'Flare Gown',
                    'score': 95.0,
                    'description': 'A sample style.',
                    'reasons': ['A recorded fabric link supports this style.'],
                    'images': [],
                    'missing_measurements': [],
                }],
            },
        )

        response = self.client.post('/recommendations/', {
            'measurement_profile_id': '12',
            'fabric_id': '7',
            'category': 'gowns',
            'limit': '5',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Flare Gown')
        self.assertContains(response, '95.0/100')
        self.assertTemplateUsed(response, 'recommendations/dashboard.html')
        self.assertTrue(mock_post.call_args.args[0].endswith('/api/v1/recommendations/'))
        self.assertEqual(mock_post.call_args.kwargs['json'], {
            'measurement_profile_id': '12',
            'fabric_id': '7',
            'category': 'gowns',
            'limit': '5',
        })

# Create your tests here.
