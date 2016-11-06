import json

class Client(object):
    def __init__(self, test_client=None, prepend=''):
        if test_client is None:
            from app import app
            self.client = app.test_client()
        else:
            self.client = test_client

        self.prepend = prepend

    def auth(self, username, password):
        """" Perform authorized request to /auth and return response"""
        rv = self.post('/auth',
                        data=json.dumps({'username': username, 'password': password})
                        )
        return rv

    def get(self, route, token=None, data=None, content_type=None,  headers=None):
        """" Perform get request to a route and return response"""
        content_type = content_type or 'application/json'

        if token is not None:
            headers = headers or {'Authorization': 'JWT %s' % token}

        return self.client.get(self.prepend + route, data=data, content_type=content_type, headers=headers)

    def post(self, route, token = None, data=None, content_type=None, follow_redirects=True, headers=None):
        """" Perform post request to a route and return response"""
        content_type = content_type or 'application/json'

        if token is not None:
            headers = headers or {'Authorization': 'Bearer ' + token}

        return self.client.post(self.prepend + route, data=data, content_type=content_type, headers=headers)
