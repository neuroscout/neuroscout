import json

def test_auth(auth_client):    
    # Test bad URL with correct auth
    rv = auth_client.get('/api/v1/hello')
    assert rv.status_code == 404

    # Get auth token with invalid credentials
    auth_resp = auth_client.post('/auth',
                        data={'username': 'not', 'password': 'existing'},
                        headers=None)
    auth_resp = json.loads(auth_resp.data.decode())
    assert auth_resp['status_code'] == 401

