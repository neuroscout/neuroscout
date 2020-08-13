import datetime
from flask_security.confirmable import confirm_user
from ...models.auth import User
from ..request_utils import decode_json


def test_auth(auth_client):
    # Get auth token with invalid credentials
    auth_resp = auth_client.post(
        '/api/auth',
        data={'username': 'not', 'password': 'existing'},
        headers=None)
    assert auth_resp.status_code == 401

    # Test without auth token
    auth_client.token = None

    resp = auth_client.get('/api/{}'.format('user'))
    assert resp.status_code == 401
    assert decode_json(resp)['description'] == \
        'Request does not contain an access token'


def test_get(auth_client):
    time = datetime.datetime.now()
    resp = auth_client.get('/api/user')
    assert resp.status_code == 200
    assert 'email' in decode_json(resp)

    user = User.query.filter_by(email=decode_json(resp)['email']).one()
    assert user.last_activity_at > time
    assert user.last_activity_ip is not None


def test_put(auth_client):
    # Testing changing name
    values = decode_json(auth_client.get('/api/user'))
    values['name'] = 'new_name'
    resp = auth_client.put('/api/user', data=values)

    assert resp.status_code == 200
    new_values = decode_json(auth_client.get('/api/user'))
    new_values['name'] = 'new_name'

    # Testing incomplete put request
    resp = auth_client.put('/api/user', data={'name': 'new_name'})
    assert resp.status_code == 200


def test_create_new(auth_client, session):
    # Make a new user and authorize
    resp = auth_client.post(
        '/api/user',
        data={
            'name': 'me', 'email': 'fake@gmail.com', 'password': 'something'})

    auth_client.authorize(email="fake@gmail.com", password="something")
    # Try getting route without confirming, should fail
    resp = auth_client.get('/api/user')
    assert resp.status_code == 401
    # Confirm new user manually

    user = User.query.filter_by(email="fake@gmail.com").one()
    confirm_user(user)
    session.commit()

    # Now should work
    resp = auth_client.get('/api/user')
    assert resp.status_code == 200
    assert decode_json(resp)['email'] == 'fake@gmail.com'


def test_post(auth_client):
    # Make incomplete post
    resp = auth_client.post('/api/user', data={'name': 'me'})
    assert resp.status_code == 422

    # Invalid email
    resp = auth_client.post(
        '/api/user',
        data={'name': 'me', 'email': 'fake'})
    assert resp.status_code == 422
    # assert 'Not a valid' in decode_json(resp)['errors']['email'][0]

    # Valid email
    resp = auth_client.post(
        '/api/user',
        data={
            'name': 'me', 'email': 'fake@gmail.com', 'password': 'something'})
    assert resp.status_code == 200


def test_get_analysis_list(auth_client):
    resp = auth_client.get('/api/user')

    user = User.query.filter_by(email=decode_json(resp)['email']).one()

    resp = auth_client.get(f'/api/user/{user.id}/analyses')
    assert len(decode_json(resp)) == 0
