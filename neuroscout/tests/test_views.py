def test_page(auth_client):
    rv = auth_client.get('/')
    assert rv.status_code == 200


def test_swagger(auth_client):
    rv = auth_client.get('/swagger/')
    assert rv.status_code == 200
