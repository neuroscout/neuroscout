import json
import pytest
from app import app

def auth(username=None, password=None):
    username = username or 'test1'
    password = password or 'test1'
    rv = post('/auth',
                    data=json.dumps({'username': username, 'password': password})
                    )
    return json.loads(rv.data.decode())

def get(route, token=None, data=None, content_type=None,  headers=None):
    content_type = content_type or 'application/json'

    if token is not None:
        headers = headers or {'Authorization': 'JWT %s' % token}

    return app.test_client().get(route, data=data, content_type=content_type, headers=headers)

def post(route, token = None, data=None, content_type=None, follow_redirects=True, headers=None):
    content_type = content_type or 'application/json'

    if token is not None:
        headers = headers or {'Authorization': 'Bearer ' + token}

    return app.test_client().post(route, data=data, content_type=content_type, headers=headers)

@pytest.mark.usefixtures("db_init")
def test_auth(add_user):    
    # Get auth token with invalid credentials
    auth_resp = auth('not', 'existing')
    assert auth_resp['status_code'] == 401

    user_name, password = add_user

    # Get auth token with valid credentials
    auth_resp = auth(user_name, password)
    assert 'access_token' in auth_resp

    token = auth_resp['access_token']
    # Get from dummy api 
    rv = get('/api/v1/hello', content_type=None, token = token)
    assert rv.status_code == 200

    data = json.loads(rv.data.decode())
    assert data == {'hello': 'world'}
