import pytest
from app import app

# @pytest.mark.usefixtures("db_init_clean")
# class TestViews:
#     def test_page(self):
#         rv = app.test_client().get('/')
#         assert rv.status_code == 200