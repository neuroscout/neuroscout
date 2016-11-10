import pytest
import json
from tests.request_utils import Client

@pytest.mark.usefixtures("db_init_clean")
def test_auth(auth_client):    
    # Get auth token with invalid credentials
    client = Client()
    auth_resp = client.auth('not', 'existing')
    auth_resp = json.loads(auth_resp.data.decode())
    assert auth_resp['status_code'] == 401

    # Test bad URL with correct auth
    rv = auth_client.get('/api/v1/hello')
    assert rv.status_code == 404

