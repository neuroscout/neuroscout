from flask_restful import Resource, abort
from flask_restful_swagger.swagger import operation
from flask_jwt import jwt_required
from marshmallow import Schema, fields
from models.run import Run

class RunSchema(Schema):
	id = fields.Str(dump_only=True)
	class Meta:
		additional = ('session', 'subject', 'number', 'task', 'duration',
					  'task_description', 'TR', 'path', 'datset_id')

class RunResource(Resource):
	""" Resource for Run """
	@operation(
	responseMessages=[
	    {
	      "code": 400,
	      "message": "Run doesn't exist"
	    },
	  ]
	)
	@jwt_required()
	def get(self, run_id):
		""" Access a run """
		result = Run.query.filter_by(id=run_id).one()
		if result:
			return RunSchema().dump(result)
		else:
			abort(400, message="Run {} doesn't exist".format(run_id))
