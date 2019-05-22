""" IO utils """
import json
import tarfile


def write_jsons(objects, base_dir):
    """ Write JSON objects to file
    Args:
        objects (list of tuples) Pairs of JSON-objects and base file name
        base_dir: Path-like directory to write to
    Returns:
        string path, base_name
    """
    results = []
    for obj, file_name in results:
        path = (base_dir / file_name).with_suffix('.json')
        json.dump(obj, path.open('w'))
        results.append(str(path), path.name)
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
