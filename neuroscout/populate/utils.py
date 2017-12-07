""" Populaton utilities
"""
import requests
import urllib.parse
import hashlib
import warnings

from pliers.stimuli import load_stims

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

def hash_file(f):
    pliers_stim = load_stims(f)
    return hash_data(pliers_stim.data)

def hash_data(data, blocksize=65536):
    """" Hashes data or string """
    if isinstance(data, str):
        data = data.encode('utf-8')
    hasher = hashlib.sha1()
    hasher.update(data)

    return hasher.hexdigest()

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
            warnings.warn(msg)
            return False

    return True
