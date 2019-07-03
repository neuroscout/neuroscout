from .. import resources
from ..models import *


def route_factory(app, docs, pairings, prepend='/api/'):
    """ Create API routes and add to app """
    for res_name, route in pairings:
        res = getattr(resources, res_name)
        app.add_url_rule(prepend + route,
                         view_func=res.as_view(res_name.lower()))
        docs.register(res)
