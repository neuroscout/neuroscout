""" Populaton utilities
"""
import requests
import urllib.parse
import hashlib
import warnings
from pathlib import Path


def hash_stim(stim, blocksize=65536):
    """ Hash a pliers stimulus """
    if isinstance(stim, Path):
        stim = stim.as_posix()
    if isinstance(stim, str):
        from pliers.stimuli import load_stims
        from os.path import isfile
        assert isfile(stim)
        stim = load_stims(stim)

    hasher = hashlib.sha1()

    if hasattr(stim, "data"):
        return hash_data(stim.data)
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
    elif hasattr(data, 'to_string'):
        data = data.to_string().encode('utf-8')
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
