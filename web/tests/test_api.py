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
    assert auth_resp.status_code == 401

def test_get_user(auth_client, add_analyses):
	rv = auth_client.get('/api/user')
	assert rv.status_code == 200

	assert 'email' in decode_json(rv)
	assert type(decode_json(rv)['analyses']) == list
	assert len(decode_json(rv)['analyses']) > 0 

def test_put_user(auth_client, add_analyses):
	# Testing changing name
	values = decode_json(auth_client.get('/api/user'))
	values['name'] = 'new_name'
	put_rv = auth_client.get('/api/user', data=values)

	assert put_rv.status_code == 200
	new_values = decode_json(auth_client.get('/api/user'))
	new_values['name'] = 'new_name'

	# Testing incomplete put request
	put_rv = auth_client.put('/api/user', data={'name' : 'new_name'})
	assert put_rv.status_code == 400
	assert 'email' in decode_json(put_rv)['errors']


def test_datasets(auth_client, add_datasets):
	rv = auth_client.get('/api/datasets')
	assert rv.status_code == 200

