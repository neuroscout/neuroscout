from flask_jwt import current_identity, jwt_required
from flask_security.recoverable import reset_password_token_status
import webargs as wa

from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
from ..models import User, Analysis
from ..database import db
from ..auth import register_user, reset_password, send_confirmation
from .utils import abort, auth_required, first_or_404
from ..utils.db import put_record
from ..schemas.user import UserSchema, UserCreationSchema, UserResetSchema
from ..schemas.predictor import PredictorSchema
from ..schemas.analysis import AnalysisSchema
from .predictor import get_predictors


@marshal_with(UserSchema)
class UserRootResource(MethodResource):
    @doc(tags=['user'], summary='Get current user information.')
    @auth_required
    def get(self):
        return current_identity

    @use_kwargs(UserCreationSchema)
    def post(self, **kwargs):
        return register_user(**kwargs)

    put_kwargs = ['name', 'picture', 'institution', 'personal_site',
                  'twitter_handle', 'orcid', 'public_email']

    @use_kwargs(UserSchema(only=put_kwargs))
    @auth_required
    def put(self, **kwargs):
        if 'email' in kwargs:
            if User.query.filter((User.email == kwargs['email'])
                                 & (User.id != current_identity.id)).all():
                abort(422, 'Email already in use.')
        return put_record(kwargs, current_identity)


@marshal_with(UserSchema)
class UserDetailResource(MethodResource):
    @doc(tags=['user'], summary='Get a given users information.')
    def get(self, user_id):
        return first_or_404(User.query.filter_by(id=user_id))

@marshal_with(AnalysisSchema(many=True))
class UserPrivateAnalysisListResource(MethodResource):
    @doc(tags=['user'], summary='Get a list of analyses created by a user.')
    @auth_required
    def get(self):
        kwargs = {'user_id': current_identity.id}
        return Analysis.query.filter_by(**kwargs)

@marshal_with(UserSchema(many=True, exclude=['predictor_collections',
                                             'first_login']))
class UserListResource(MethodResource):
    @doc(tags=['user'], summary='Get a list of public users.')
    def get(self):
        return User.query.all()


@marshal_with(AnalysisSchema(many=True))
class UserAnalysisListResource(MethodResource):
    @doc(tags=['user'], summary='Get a list of analyses created by a user.')
    def get(self, user_id):
        kwargs = {'user_id': user_id, 'private': False, 'status': 'PASSED'}
        return Analysis.query.filter_by(**kwargs)


class UserResendConfirm(MethodResource):
    @jwt_required()
    def post(self):
        if send_confirmation(current_identity):
            resp = {'message': 'Confirmation resent'}
        else:
            resp = {'message': 'User is already confirmed'}
        return resp

# @doc(tags=['auth'], summary='Request a password reset token.')
@use_kwargs(UserSchema(only=['email']))
class UserTriggerResetResource(MethodResource):
    def post(self, **kwargs):
        reset_password(kwargs['email'])
        return {'message': 'Password reset token sent'}

# @doc(tags=['auth'], summary='Reset user password using a token.')
@use_kwargs(UserResetSchema(only=['token', 'password']))
class UserResetSubmitResource(MethodResource):
    def post(self, **kwargs):
        expired, invalid, user = reset_password_token_status(kwargs['token'])
        if expired:
            abort(422, 'Password reset token expired.')
        elif invalid:
            abort(422, 'Invalid password reset token.')
        else:
            user.password = kwargs['password']
            db.session.commit()
            return {'message': 'Password reset succesfully.'}


class UserPredictorListResource(MethodResource):
    @doc(tags=['user'], summary='Get list of user predictors.',)
    @use_kwargs({
        'run_id': wa.fields.DelimitedList(
            wa.fields.Int(), description="Run id(s). Warning, slow query."),
        'name': wa.fields.DelimitedList(wa.fields.Str(),
                                        description="Predictor name(s)"),
        'newest': wa.fields.Boolean(
            missing=True,
            description="Return only newest Predictor by name")
        },
        locations=['query'])
    @auth_required
    @marshal_with(PredictorSchema(many=True))
    def get(self, **kwargs):
        newest = kwargs.pop('newest')
        return get_predictors(newest=newest, user=current_identity,
                              **kwargs)
