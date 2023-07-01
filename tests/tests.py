import unittest

from flask import session
from main import app


class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        app.testing = True
        app.debug = True
        self.client = app.test_client()

    def test_home_route_without_logging_in(self):
        with app.test_client() as client:
            response = client.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Inicio', response.data)

    def test_home_route_after_logging_in(self):
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['logged_in'] = True
            response = client.get('/')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, '/dashboard')

    def test_set_default_language(self):
        with app.test_client() as client:
            response = client.get('/')
            self.assertEqual(session['language'], 'es')

    def test_set_language(self):
        with app.test_request_context('/', method='GET'):
            session['language'] = 'en'
            response = self.client.get('/')
            self.assertEqual(session['language'], 'en')

    def test_login_route_post_successful(self):
        response = self.client.post('/login', data=dict(
            email='info@beedataanalytics.com',
            password='beedata23TFG'
        ))
        self.assertEqual(response.location, '/dashboard')

    def test_login_route_post_unsuccessful(self):
        response = self.client.post('/login', data=dict(
            email='test@example.com',
            password='incorrect_password'
        ))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Error', response.data)

    def test_login_route_get(self):
        response = self.client.post('/login', data=dict(
            email='test@example.com',
            password='incorrect_password'
        ))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Inici', response.data)

    def test_logout_route(self):
        with app.test_request_context('/logout', method='GET'):
            response = self.client.get('/logout')
            self.assertEqual(response.location, '/')
            self.assertEqual(session, {})
            self.assertEqual(session.get('logged_in'), None)

    def test_dashboard_route(self):
        with app.test_request_context('/dashboard', method='GET'):
            self.client.post('/login', data=dict(
                email='info@beedataanalytics.com',
                password='beedata23TFG'
            ))
            response = self.client.get('/dashboard')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'PROY', response.data)

    def test_dashboard_route_without_logging_in(self):
        with app.test_request_context('/dashboard', method='GET'):
            response = self.client.get('/dashboard')
            self.assertIn(b'Inici', response.data)
            self.assertEqual(session, {})
            self.assertEqual(session.get('logged_in'), None)

    def test_add_time_entry(self):
        with app.test_request_context('/dashboard', method='GET'):
            self.client.post('/login', data=dict(
                email='info@beedataanalytics.com',
                password='beedata23TFG'
            ))
            task_id = '36734334'
            description = 'hola'
            date_str = '2023-06-28'
            time = '20:58'
            hours = '33'
            minutes = '33'
            tags = 'test'

            # Simular la solicitud POST
            response = self.client.post('/add_time_entry', data={
                'taskId': task_id,
                'description': description,
                'date': date_str,
                'time': time,
                'hours': hours,
                'minutes': minutes,
                'tags': tags
            })

            # Verificar que se redirige a la página correcta
            self.assertEqual(response.location, '/dashboard')

    def test_add_time_entry_no_session(self):
        # Simular que el usuario no ha iniciado sesión
        with self.client.session_transaction() as sess:
            sess.pop('logged_in', None)

        # Simular la solicitud POST
        response = self.client.post('/add_time_entry')

        # Verificar que se renderiza el template de login
        self.assertIn(b'Inicio', response.data)

    def test_task_details_route(self):
        with app.test_request_context('/dashboard', method='GET'):
            self.client.post('/login', data=dict(
                email='info@beedataanalytics.com',
                password='beedata23TFG'
            ))
            response = self.client.get('/task_details/36734334')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Reg', response.data)

    def test_task_details_route_without_logging_in(self):
        with app.test_request_context('/dashboard', method='GET'):
            response = self.client.get('/task_details/36734334')
            self.assertIn(b'Inici', response.data)
            self.assertEqual(session, {})
            self.assertEqual(session.get('logged_in'), None)

    def test_task_details_route_with_invalid_task_id(self):
        with app.test_request_context('/dashboard', method='GET'):
            self.client.post('/login', data=dict(
                email='info@beedataanalytics.com',
                password='beedata23TFG'
            ))
            response = self.client.get('/task_details/invalid_task_id')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, '/dashboard')

    def test_showResults_route(self):
        with app.test_request_context('/dashboard', method='GET'):
            self.client.post('/login', data=dict(
                email='info@beedataanalytics.com',
                password='beedata23TFG'
            ))
            response = self.client.get('/show_results/tasca')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'RESULTA', response.data)

    def test_showResults_bad_query(self):
        with app.test_request_context('/dashboard', method='GET'):
            self.client.post('/login', data=dict(
                email='info@beedataanalytics.com',
                password='beedata23TFG'
            ))
            response = self.client.get('/show_results/adafaf')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'No se enco', response.data)

    def test_delete_task_success(self):
        with app.test_request_context('/dashboard', method='GET'):
            self.client.post('/login', data=dict(
                email='info@beedataanalytics.com',
                password='beedata23TFG'
            ))

            response = self.client.delete('/delete_task/36734334')
            self.assertEqual(response.json['success'], True)

    def test_delete_task_error(self):
        with app.test_request_context('/dashboard', method='GET'):
            self.client.post('/login', data=dict(
                email='info@beedataanalytics.com',
                password='beedata23TFG'
            ))

            response = self.client.delete('/delete_task/aaaa')
            self.assertEqual(response.json['success'], False)


if __name__ == '__main__':
    unittest.main()
