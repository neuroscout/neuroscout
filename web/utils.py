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
