'''
Test basic views
'''


def test_swagger(auth_client):
    rv = auth_client.get('/swagger/')
    assert rv.status_code == 200
