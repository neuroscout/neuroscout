import json
import re
from pliers import extractors as piext
from flask_apispec import MethodResource, marshal_with, doc
from flask import current_app
from ..core import cache
from ..schemas.extractor import ExtractorSchema


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
