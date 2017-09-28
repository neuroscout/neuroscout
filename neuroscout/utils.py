import requests
import urllib.parse

def hash_file(f, blocksize=65536):
    import hashlib
    hasher = hashlib.sha1()
    with open(f, 'rb') as afile:
        buf = afile.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(blocksize)
    return hasher.hexdigest()

def hash_str(string, blocksize=65536):
    import hashlib
    hasher = hashlib.sha1()
    hasher.update(string.encode('utf-8'))

    return hasher.hexdigest()

def route_factory(app, docs, pairings, prepend='/api/'):
    import resources
    for res_name, route in pairings:
        res = getattr(resources, res_name)
        app.add_url_rule(prepend + route,
                         view_func=res.as_view(res_name.lower()))
        docs.register(res)

def generate_id(n=6):
    import random
    import string

    return ''.join(random.SystemRandom().choice(
        string.ascii_uppercase + string.digits) for _ in range(n))

def remote_resource_exists(base_address, resource, raise_exception=False,
                 content_type='binary/octet-stream'):
    address = urllib.parse.urljoin(base_address, resource)
    r = requests.head(address)
    if not r.ok or r.headers.get('Content-Type') != content_type:
        msg = "Remote resource {} not found".format(address)
        if raise_exception:
            raise ValueError(msg)
        else:
            import warnings
            warnings.warn(msg)
            return False

    return True
