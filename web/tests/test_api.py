import pytest
import json
from tests.request_utils import auth, get

@pytest.mark.usefixtures("db_init")
def test_auth(valid_auth_resp):    
    # Get auth token with invalid credentials
    auth_resp = auth('not', 'existing')
    assert auth_resp['status_code'] == 401

    # Get auth token with valid credentials
    assert 'access_token' in valid_auth_resp

    token = valid_auth_resp['access_token']

    # Test bad URL with correct auth
    rv = get('/api/v1/hello', token = token)
    assert rv.status_code == 404

