# -*- coding: utf-8 -*-
""" Core Neuroscout App """
from flask import send_file, render_template, url_for
from .basic import create_app
from .models import db, user_datastore
from .admin import admin_factory

app, cache = create_app()

from flask_mail import Mail
from flask_jwt import JWT
from flask_security import Security
from flask_security.confirmable import confirm_email_token_status, confirm_user
from flask_cors import CORS
from flask_admin import Admin

app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
admin = Admin(app, name='Neuroscout-Admin', template_mode='bootstrap3')

admin_factory(['User', 'Analysis', 'Dataset'], db.session, admin)

mail = Mail(app)
# Enable CORS
cors = CORS(
    app,
    resources={r"/api/*": {"origins": "*"}, r"/swagger/": {"origins": "*"}})

# These imports require the above
from .auth import authenticate, load_user
from .utils.factory import route_factory
from .api_spec import docs

# Setup Flask-Security and JWT
security = Security(app, user_datastore)
jwt = JWT(app, authenticate, load_user)

# Set up API routes
route_factory(
    app, docs,
    [
        ('DatasetResource', 'datasets/<int:dataset_id>'),
        ('DatasetListResource', 'datasets'),
        ('DatasetAnalysisListResource', 'datasets/<int:dataset_id>/analyses'),
        ('AnalysisRootResource', 'analyses'),
        ('AnalysisResource', 'analyses/<analysis_id>'),
        ('AnalysisFullResource', 'analyses/<analysis_id>/full'),
        ('AnalysisUploadResource', 'analyses/<analysis_id>/upload'),
        ('BibliographyResource', 'analyses/<analysis_id>/bibliography'),
        ('CloneAnalysisResource', 'analyses/<analysis_id>/clone'),
        ('CompileAnalysisResource', 'analyses/<analysis_id>/compile'),
        ('ReportResource', 'analyses/<analysis_id>/report'),
        ('AnalysisResourcesResource', 'analyses/<analysis_id>/resources'),
        ('AnalysisBundleResource', 'analyses/<analysis_id>/bundle'),
        ('AnalysisFillResource', 'analyses/<analysis_id>/fill'),
        ('RunListResource', 'runs'),
        ('RunResource', 'runs/<int:run_id>'),
        ('RunTimingResource', 'runs/<int:run_id>/timing'),
        ('PredictorListResource', 'predictors'),
        ('PredictorResource', 'predictors/<int:predictor_id>'),
        ('PredictorRelatedResource', 'predictors/<predictor_id>/related'),
        ('PredictorCollectionResource', 'predictors/collection/<int:pc_id>'),
        ('PredictorCollectionCreateResource', 'predictors/collection'),
        ('PredictorEventListResource', 'predictor-events'),
        ('UserRootResource', 'user'),
        ('UserDetailResource', 'user/<string:user_name>'),
        ('UserAnalysisListResource', 'user/<string:user_name>/analyses'),
        ('UserPrivateAnalysisListResource', 'user/myanalyses'),
        ('UserListResource', 'users'),
        ('UserTriggerResetResource', 'user/reset_password'),
        ('UserResetSubmitResource', 'user/submit_token'),
        ('UserResendConfirm', 'user/resend_confirmation'),
        ('UserPredictorListResource', 'user/predictors'),
        ('UserPredictorCollectionResource', 'user/collections'),
        ('TaskResource', 'tasks/<int:task_id>'),
        ('TaskPredictorsResource', 'tasks/<int:task_id>/predictors'),
        ('TaskListResource', 'tasks'),
        ('ImageVersionResource', 'image_version'),
        ('ExtractorListResource', 'extractors'),
        ('ExtractorDistinctResource', 'extractors/distinct')
    ])


@app.route('/confirm/<token>')
def confirm(token):
    ''' Serve confirmaton page '''
    expired, invalid, user = confirm_email_token_status(token)
    name, confirmed = None, None
    if user:
        if not expired and not invalid:
            confirmed = confirm_user(user)
            db.session.commit()
        name = user.name
    else:
        confirmed = None
    return render_template(
        'confirm.html', confirmed=confirmed, expired=expired, invalid=invalid,
        name=name, action_url=url_for('index', _external=True))

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    ''' Serve index '''
    return send_file("frontend/build/index.html")
