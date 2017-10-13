"""
    Misc. utilities useful across package.
"""
import requests
import urllib.parse

def hash_file(f, blocksize=65536):
    """ Hash a file, given a file name string """
    import hashlib
    hasher = hashlib.sha1()
    with open(f, 'rb') as afile:
        buf = afile.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(blocksize)
    return hasher.hexdigest()

def hash_str(string, blocksize=65536):
    """" Hash a string """
    import hashlib
    hasher = hashlib.sha1()
    hasher.update(string.encode('utf-8'))

    return hasher.hexdigest()

def route_factory(app, docs, pairings, prepend='/api/'):
    """ Create API routes and add to app """
    import resources
    for res_name, route in pairings:
        res = getattr(resources, res_name)
        app.add_url_rule(prepend + route,
                         view_func=res.as_view(res_name.lower()))
        docs.register(res)

def remote_resource_exists(base_address, resource, raise_exception=False,
                 content_type='binary/octet-stream'):
    """ Check if a remote address exists and content_type matches """
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

def format_preproc(subject, task, run, session=None,
                   space="MNI152NLin2009cAsym", suffix="preproc"):
    """ Format relative fmri_prep paths """
    subject_f = "sub-{}/".format(subject)
    session_f = "ses-{}/".format(session) if session else ""

    return "{}{}func/{}{}task-{}_run-{}_bold_space-{}_{}.nii.gz".format(
    subject_f, session_f,
    subject_f.replace("/", "_"), session_f.replace("/", "_"),
    task, run, space, suffix
)
