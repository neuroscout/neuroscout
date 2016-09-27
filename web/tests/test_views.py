import pytest
from app import app

@pytest.mark.usefixtures("flask_init")
class TestViews:
    def test_page(self):
        rv = app.test_client().get('/')
        assert rv.status_code == 200