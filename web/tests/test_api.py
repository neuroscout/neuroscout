import json
import pytest
from app import app

@pytest.mark.usefixtures("flask_init")
class TestAPI:
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
        return app.test_client().get(route, data=data, content_type=content_type, headers=headers)

    def _post(self, route, data=None, content_type=None, follow_redirects=True, headers=None):
        content_type = content_type or 'application/json'
        if hasattr(self, 'token'):
            headers = headers or {'Authorization': 'Bearer ' + self.token}
        return app.test_client().post(route, data=data, content_type=content_type, headers=headers)

    def test_auth(self):
        # Get auth token with invalid credentials
        auth_resp = self._auth('not', 'existing')
        assert auth_resp['status_code'] == 401

        # Get auth token with valid credentials
        auth_resp = self._auth('test1', 'test1')
        assert 'access_token' in auth_resp

        self.token = auth_resp['access_token']

        # Get from dummy api 
        rv = self._get('/api/v1/hello', content_type=None)
        assert rv.status_code == 200
        data = json.loads(rv.data.decode())
        assert data == {'hello': 'world'}
