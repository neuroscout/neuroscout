import json
from app import app

def auth(username, password):
    """" Perform authorized request to /auth and return response"""
    rv = post('/auth',
                    data=json.dumps({'username': username, 'password': password})
                    )
    return json.loads(rv.data.decode())

def get(route, token=None, data=None, content_type=None,  headers=None):
    """" Perform get request to a route and return response"""
    content_type = content_type or 'application/json'

    if token is not None:
        headers = headers or {'Authorization': 'JWT %s' % token}

    return app.test_client().get(route, data=data, content_type=content_type, headers=headers)

def post(route, token = None, data=None, content_type=None, follow_redirects=True, headers=None):
    """" Perform post request to a route and return response"""
    content_type = content_type or 'application/json'

    if token is not None:
        headers = headers or {'Authorization': 'Bearer ' + token}

    return app.test_client().post(route, data=data, content_type=content_type, headers=headers)
