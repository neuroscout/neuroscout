import pytest
import json
from request_utils import auth, get

@pytest.fixture(scope="session")
def valid_auth_resp(add_user):
    username, password = add_user
    return auth(username, password)

@pytest.mark.usefixtures("db_init")
def test_auth(valid_auth_resp):    
    # Get auth token with invalid credentials
    auth_resp = auth('not', 'existing')
    assert auth_resp['status_code'] == 401

    # Get auth token with valid credentials
    assert 'access_token' in valid_auth_resp

    token = valid_auth_resp['access_token']
    # Get from dummy api 
    rv = get('/api/v1/hello', content_type=None, token = token)
    assert rv.status_code == 200

    data = json.loads(rv.data.decode())
    assert data == {'hello': 'world'}
