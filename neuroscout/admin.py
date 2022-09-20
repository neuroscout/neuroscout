from . import models
from flask_admin.contrib.sqla import ModelView

def admin_factory(model_list, db_session, admin):
    for m_name in model_list:
        model = getattr(models, m_name)
        admin.add_view(ModelView(model, db_session))
