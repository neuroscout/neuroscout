def test_page(auth_client):
    rv = auth_client.get('/')
    assert rv.status_code == 200