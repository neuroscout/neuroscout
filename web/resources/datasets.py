from flask_restful import Resource, abort
from flask_jwt import jwt_required
from marshmallow import Schema, fields
from models import Dataset

class DatasetResource(Resource):
	@jwt_required()
	def get(self, dataset_id):
		ds = Dataset.query.filter_by(external_id=dataset_id).first()
		if ds:
			schema = DatasetSchema()
			return schema.dump(ds)
		else:
			abort(404, message="Dataset {} doesn't exist".format(dataset_id))

	def put(self, dataset_id):
		pass

class DatasetSchema(Schema):
	name = fields.Str()
	external_id = fields.Str()


class DatasetListResource(Resource):
	@jwt_required()
	def get(self):
		pass
	def put(self):
		pass