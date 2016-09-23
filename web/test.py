import os
import unittest
import tempfile
import re
import json

from flask_security.utils import encrypt_password
from flask_security import current_user
from flask_security.utils import login_user

from models import User, Role, Dataset
from app import app, user_datastore
from database import db

class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        if os.environ['APP_SETTINGS'] != 'config.TravisConfig':
            app.config.from_object('config.TestingConfig')
        self.client = app.test_client()

        db.init_app(app)
        with app.app_context():
            db.create_all()
            user_datastore.create_user(email='test1', password=encrypt_password('test1'))
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()


class APITest(FlaskTestCase):
    def _auth(self, username=None, password=None):
        username = username or 'test1'
        password = password or 'test1'
        rv = self._post('/auth',
                        data=json.dumps({'username': username, 'password': password})
                        )
        return json.loads(rv.data.decode())

    def _get(self, route, data=None, content_type=None,  headers=None):
        content_type = content_type or 'application/json'
        if hasattr(self, 'token'):
            headers = headers or {'Authorization': 'JWT %s' % self.token}
        return self.client.get(route, data=data, content_type=content_type, headers=headers)

    def _post(self, route, data=None, content_type=None, follow_redirects=True, headers=None):
        content_type = content_type or 'application/json'
        if hasattr(self, 'token'):
            headers = headers or {'Authorization': 'Bearer ' + self.token}
        return self.client.post(route, data=data, content_type=content_type, headers=headers)

    def test_auth(self):
        # Get auth token with invalid credentials
        auth_resp = self._auth('not', 'existing')
        self.assertEqual(401, auth_resp['status_code'])

        # Get auth token with valid credentials
        auth_resp = self._auth('test1', 'test1')
        self.assertIn(u'access_token', auth_resp)

        self.token = auth_resp['access_token']

        # Get from dummy api 
        rv = self._get('/dummy-api', content_type=None)
        self.assertEqual(200, rv.status_code)
        data = json.loads(rv.data.decode())
        self.assertEqual(data['items'], {u'Key1': u'Value1', u'Key2': u'value2'})

class ModelsTest(FlaskTestCase):
    def test_dataset(self):
        with app.app_context():
            instance = Dataset(name='test dataset!')
            db.session.add(instance)
            db.session.commit()
            self.assertTrue(hasattr(instance, 'id'))

class ViewsTest(FlaskTestCase):
    def test_page(self):
        rv = self.client.get('/')
        self.assertEqual(200, rv.status_code)


if __name__ == '__main__':
    unittest.main()
