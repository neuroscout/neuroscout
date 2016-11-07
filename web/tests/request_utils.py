import json

class Client(object):
    def __init__(self, test_client=None, prepend='', username=None, password=None):
        if test_client is None:
            from app import app
            self.client = app.test_client()
            self.client_flask = True
        else:
            self.client = test_client
            self.client_flask = False

        self.prepend = prepend
        self.token = None

        if username is not None and password is not None:
            self.username = username
            self.password = password
            self.reauthorize()
    def _get_headers(self, token):
        if token is not None:
            return {'Authorization': 'JWT %s' % token}
        elif self.token is not None:
           return {'Authorization': 'JWT %s' % self.token}

    def auth(self, username, password):
        """" Perform authorized request to /auth and return response"""
        rv = self.post('/auth',
                        data={'username': username, 'password': password}
                        )
        return rv

    def reauthorize(self):
        self.token = self.auth(self.username, self.password).json()['access_token']

    def get(self, route, token=None, data=None, headers=None):
        """" Perform get request to a route and return response"""
        headers = headers or self._get_headers(token)

        if self.client_flask:
            return self.client.get(self.prepend + route, data=json.dumps(data), 
                content_type='application/json', headers=headers)
        else:
            return self.client.get(self.prepend + route, json=data, 
                headers=headers)

    def post(self, route, token = None, data=None, follow_redirects=True, headers=None):
        """" Perform post request to a route and return response"""
        headers = headers or self._get_headers(token)

        if self.client_flask:
            return self.client.post(self.prepend + route, data=json.dumps(data), 
                content_type='application/json', headers=headers)
        else:
            return self.client.post(self.prepend + route, json=data, 
                headers=headers)

    def put(self, route, token = None, data=None, follow_redirects=True, headers=None):
        """" Perform post request to a route and return response"""
        headers = headers or self._get_headers(token)

        if self.client_flask:
            return self.client.post(self.prepend + route, data=json.dumps(data), 
                content_type='application/json', headers=headers)
        else:
            return self.client.put(self.prepend + route, json=data, 
                headers=headers)
