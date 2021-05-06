import json
import re
from webargs import fields
from pliers import extractors as piext
from flask_apispec import MethodResource, use_kwargs, marshal_with, doc
from flask import current_app
from ..core import cache
from ..schemas.extractor import ExtractorSchema
from ..utils.misc import distinct_extractors

class ExtractorListResource(MethodResource):
    @doc(tags=['extractor'], summary='Extractor descriptions')
    @cache.cached(60 * 60 * 24 * 300, query_string=True)
    @marshal_with(ExtractorSchema(many=True))
    def get(self, **kwargs):
        schema = json.load(open(current_app.config['FEATURE_SCHEMA']))

        result = []
        extractors = schema.keys()
        for ext in extractors:
            try:
                docstring = getattr(piext, ext).__doc__

                # Only return docstring prior to Args section
                desc = docstring.split('Args')[0].replace('\n', '').strip(' ')
                desc = re.sub('\\s+', ' ', desc)  # Replace multiple spaces
                result.append({
                    'name': ext,
                    'description': desc
                    })
            except AttributeError:
                pass

        return result


class ExtractorDistinctResource(MethodResource):
    @doc(tags=['extractor'], summary='Extractor counts by dataset/task')
    @cache.cached(60 * 60 * 24 * 300, query_string=True)
    @use_kwargs({
        'count': fields.Boolean(
            missing=True,
            description="Return counts, or distinct names"),
        'active_only': fields.Boolean(
            missing=True,
            description="Return results only for active Datasets")
        },
        location='query')
    @marshal_with(ExtractorSchema(many=True))
    def get(self, **kwargs):
        count = kwargs.pop('count')
        active = kwargs.pop('active_only')

        return distinct_extractors(count=count, active=active)
