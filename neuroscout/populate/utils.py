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

def hash_stim(f, blocksize = 65536):
    """ Hash a pliers stimulus """
    if isinstance(f, str):
        stim = load_stims(f)

    hasher = hashlib.sha1()

    if hasattr(stim, "data"):
        hasher.update(stim.data)
    else:
        filename = stim.history.source_file \
                    if stim.history \
                    else stim.filename
        with open(filename, 'rb') as afile:
            buf = afile.read(blocksize)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(blocksize)

    return hasher.hexdigest()

def hash_data(data):
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
