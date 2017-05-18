import json

def decode_json(resp):
	return json.loads(resp.data.decode())

def test_auth(auth_client):
	# Test bad URL with correct auth
	resp = auth_client.get('/api/v1/hello')
	assert resp.status_code == 404

	# Get auth token with invalid credentials
	auth_resp = auth_client.post('/auth',
						data={'username': 'not', 'password': 'existing'},
						headers=None)
	assert auth_resp.status_code == 401

	# Test without auth token
	auth_client.token = None

	resp = auth_client.get('/api/{}'.format('user'))
	assert resp.status_code == 401
	assert decode_json(resp)['description'] == 'Request does not contain an access token'

def test_get(auth_client):
	resp = auth_client.get('/api/user')
	assert resp.status_code == 200

	assert 'email' in decode_json(resp)

# def test_put(auth_client):
# 	# Testing changing name
# 	values = decode_json(auth_client.get('/api/user'))
# 	values['name'] = 'new_name'
# 	resp = auth_client.get('/api/user', data=values)
#
# 	assert resp.status_code == 200
# 	new_values = decode_json(auth_client.get('/api/user'))
# 	new_values['name'] = 'new_name'
#
# 	# Testing incomplete put request
# 	resp = auth_client.put('/api/user', data={'name' : 'new_name'})
# 	assert resp.status_code == 400
# 	assert 'email' in decode_json(resp)['errors']

def test_post(auth_client):
	# Make incomplete post
	resp = auth_client.post('/api/user', data = {'name' : 'me'})
	assert resp.status_code == 422

	# Invalid email
	resp = auth_client.post('/api/user',
		data = {'name' : 'me', 'email' : 'fake'})
	assert resp.status_code == 422
	# assert 'Not a valid' in decode_json(resp)['errors']['email'][0]

	# Valid email
	resp = auth_client.post('/api/user',
		data = {'name' : 'me', 'email' : 'fake@gmail.com', 'password' : 'something'})
	assert resp.status_code == 200
