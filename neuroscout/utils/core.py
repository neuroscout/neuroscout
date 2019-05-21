"""
    Misc. utilities useful across package.
"""
from .. import resources

def route_factory(app, docs, pairings, prepend='/api/'):
    """ Create API routes and add to app """
    for res_name, route in pairings:
        res = getattr(resources, res_name)
        app.add_url_rule(prepend + route,
                         view_func=res.as_view(res_name.lower()))
        docs.register(res)

def listify(obj):
    ''' Wraps all non-list or tuple objects in a list; provides a simple way
    to accept flexible arguments. '''
    return obj if isinstance(obj, (list, tuple, type(None))) else [obj]
