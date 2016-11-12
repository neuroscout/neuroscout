import json

def decode_json(rv):
	return json.loads(rv.data.decode())

def test_auth(auth_client):    
    # Test bad URL with correct auth
    rv = auth_client.get('/api/v1/hello')
    assert rv.status_code == 404

    # Get auth token with invalid credentials
    auth_resp = auth_client.post('/auth',
                        data={'username': 'not', 'password': 'existing'},
                        headers=None)
    auth_resp = decode_json(auth_resp)
    assert auth_resp['status_code'] == 401

def test_user(auth_client, add_analyses):
	rv = auth_client.get('/api/user')
	assert rv.status_code == 200

	assert 'email' in decode_json(rv)
	assert type(decode_json(rv)['analyses']) == list
	assert len(decode_json(rv)['analyses']) > 0 



def test_datasets(auth_client, add_datasets):
	rv = auth_client.get('/api/datasets')
	assert rv.status_code == 200

