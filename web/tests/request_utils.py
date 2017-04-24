import json

class Client(object):
    def __init__(self, test_client=None, prepend='', username=None, password=None):
        if test_client is None:
            from app import app
            test_client = app.test_client()
            self.client_flask = True
        else:
            self.client_flask = False

        self.client = test_client
        self.prepend = prepend
        self.token = None

        if username is not None and password is not None:
            self.username = username
            self.password = password
            self.authorize(username, password)

    def _get_headers(self):
        if self.token is not None:
           return {'Authorization': 'JWT %s' % self.token}
        else:
            return None

    def _make_request(self, request, route, params, data, headers):
        """ Generic request handler """
        request_function = getattr(self.client, request)
        headers = headers or self._get_headers()

        if self.client_flask:
            return request_function(self.prepend + route, data=json.dumps(data),
                content_type='application/json', headers=headers)
        else:
            return request_function(self.prepend + route, json=data,
                headers=headers, params=params)

    def authorize(self, username=None, password=None):
        if username is not None and password is not None:
            self.username = username
            self.password = password

        rv = self.post('/auth',
                        data={'username': self.username, 'password': self.password})

        if self.client_flask:
             self.token = json.loads(rv.data.decode())['access_token']
        else:
            self.token = rv.json()['access_token']

    def get(self, route, params=None, data=None, headers=None):
        return self._make_request('get', route, params, data, headers)

    def post(self, route, params=None, data=None, headers=None):
        return self._make_request('post', route, params, data, headers)

    def put(self, route, params=None, data=None, headers=None):
        return self._make_request('put', route, params, data, headers)

def decode_json(rv):
    return json.loads(rv.data.decode())
