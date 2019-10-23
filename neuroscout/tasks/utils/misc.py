""" utils """
import json
import tarfile
from grabbit.extensions.writable import build_path
from ...utils.db import put_record

REPORT_PATHS = ['sub-{subject}_[ses-{session}_]task-{task}_'
                '[acq-{acquisition}_][run-{run}_]{type}.{extension}']


def update_record(model, exception=None, **fields):
    if exception is not None:
        if 'traceback' in fields:
            fields['traceback'] = f"{fields['traceback']}. \
             Error:{str(exception)}"
        if 'status' not in fields:
            fields['status'] = 'FAILED'
    put_record(fields, model)
    return fields


def write_jsons(objects, base_dir):
    """ Write JSON objects to file
    Args:
        objects (list of tuples) Pairs of JSON-objects and base file name
        base_dir: Path-like directory to write to
    Returns:
        string path, base_name
    """
    results = []
    for obj, file_name in objects:
        path = (base_dir / file_name).with_suffix('.json')
        json.dump(obj, path.open('w'))
        results.append((str(path), path.name))
    return results


def write_tarball(paths, filename):
    """ Write tarball of files in paths
    Args:
        paths (list): list of file paths to include
        filename (str): full path name of tarball
    """
    with tarfile.open(filename, "w:gz") as tar:
        for path, arcname in paths:
            tar.add(path, arcname=arcname)


class PathBuilder():
    def __init__(self, outdir, domain, hash, entities):
        self.outdir = outdir
        prepend = "https://" if "neuroscout.org" in domain else "http://"
        self.domain = prepend + domain
        self.hash = hash
        self.entities = entities

    def build(self, type, extension):
        file = build_path(
            {**self.entities, 'type': type, 'extension': extension},
            path_patterns=REPORT_PATHS)
        outfile = str(self.outdir / file)

        return outfile, '{}/reports/{}/{}'.format(self.domain, self.hash, file)
