# Setup API docs and Swagger
from .core import app
from .auth import add_auth_to_swagger
from apispec import APISpec
from flask_apispec.extension import FlaskApiSpec
from webargs import fields
from apispec.ext.marshmallow import MarshmallowPlugin

file_plugin = MarshmallowPlugin()
spec = APISpec(
    title='neuroscout',
    version='v1',
    plugins=[file_plugin],
    openapi_version='2.0'
)
app.config.update({
    'APISPEC_SPEC': spec})
add_auth_to_swagger(spec)

docs = FlaskApiSpec(app)


@file_plugin.map_to_openapi_type('file', None)
class FileField(fields.Raw):
    pass
