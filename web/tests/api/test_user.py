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

	# Test without auth token
	auth_client.token = None
	domains = ['user', 'datasets', 'analyses']

	for domain in domains:
		rv = auth_client.get('/api/{}'.format(domain))
		assert rv.status_code == 401
		assert decode_json(rv)['description'] == 'Request does not contain an access token'

def test_get(auth_client, add_analyses):
	rv = auth_client.get('/api/user')
	assert rv.status_code == 200

	assert 'email' in decode_json(rv)
	assert type(decode_json(rv)['analyses']) == list
	assert len(decode_json(rv)['analyses']) > 0

def test_put(auth_client, add_analyses):
	# Testing changing name
	values = decode_json(auth_client.get('/api/user'))
	values['name'] = 'new_name'
	rv = auth_client.get('/api/user', data=values)

	assert rv.status_code == 200
	new_values = decode_json(auth_client.get('/api/user'))
	new_values['name'] = 'new_name'

	# Testing incomplete put request
	rv = auth_client.put('/api/user', data={'name' : 'new_name'})
	assert rv.status_code == 400
	assert 'email' in decode_json(rv)['errors']

def test_post(auth_client):
	# Make incomplete post
	rv = auth_client.post('/api/user', data = {'name' : 'me'})
	assert rv.status_code == 400
	assert 'Missing data' in decode_json(rv)['errors']['email'][0]

	# Invalid email
	rv = auth_client.post('/api/user',
		data = {'name' : 'me', 'email' : 'fake'})
	assert rv.status_code == 400
	assert 'Not a valid' in decode_json(rv)['errors']['email'][0]

	# Invalid email
	rv = auth_client.post('/api/user',
		data = {'name' : 'me', 'email' : 'fake@gmail.com', 'password' : 'something'})
	assert rv.status_code == 200
