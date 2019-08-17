"""
    buckets

    stores blobs of data
"""

import os
import uuid



def mkdir_p(path):
    """make a directory path

    Makes a directory path.  If it already exists
    then return without doing anything.
    """
    if not os.path.isdir(path):
        os.makedirs(path)


def new_id():
    """Generate a random unique id"""
    return uuid.uuid4().hex


class FileBucket(object):
    """File Bucket

    FileBucket can store and retreive blobs of binary data.  This is
    useful for storing images or files as attachments where you want
    to put the binary data somewhere and be able to retreive it later
    if asked.  The id returned is generally stored in a database or
    somewhere else where it is associated with other entities in the
    system.

    FileBucket stores directly into a folder on the drive of the web
    server where it has sufficient permissions to do so.  This is a
    potential attack area so be careful to take the appropriate
    precautions.

    The location of the buckets is determined by [data] path setting
    in the site.ini configuration file.

    >>> import zoom
    >>> site = zoom.sites.Site()
    >>> path = os.path.join(site.data_path, 'buckets')
    >>> ids = ['id_%04d' % (9-i) for i in range(10)]
    >>> new_id = ids.pop

    >>> bucket = Bucket(path, new_id)
    >>> item_id = bucket.put(b'some data')
    >>> item_id
    'id_0000'
    >>> bucket.get(item_id)
    b'some data'
    >>> bucket.exists(item_id)
    True
    >>> bucket.delete(item_id)
    >>> bucket.exists(item_id)
    False

    >>> data = ('%r' % list(range(10))).encode('utf8')
    >>> item_id = bucket.put(data)
    >>> item_id
    'id_0001'
    >>> bucket.exists(item_id)
    True
    >>> bucket.get(item_id)
    b'[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]'
    >>> bucket.delete(item_id)

    >>> bucket = Bucket(path, new_id)
    >>> bucket.put(b'some data')
    'id_0002'
    >>> bucket.put(b'some more data')
    'id_0003'
    >>> sorted(bucket.keys())
    ['id_0002', 'id_0003']
    >>> for item_id in bucket.keys():
    ...     bucket.delete(item_id)
    """

    def __init__(self, path, id_factory=new_id):
        self.path = os.path.realpath(path)
        self.id_factory = id_factory
        mkdir_p(self.path)

    def put(self, item):
        item_id = self.id_factory()
        pathname = os.path.join(self.path, item_id)
        if os.path.exists(pathname):
            raise Exception('duplicate item')
        f = open(os.path.join(pathname), 'wb')
        try:
            f.write(item)
        finally:
            f.close()
        return item_id

    def get(self, item_id, default=None):
        pathname = os.path.join(self.path, item_id)
        if not os.path.exists(pathname) and default is not None:
            return default
        with open(os.path.join(pathname), 'rb') as f:
            return f.read()

    def delete(self, item_id):
        pathname = os.path.join(self.path, item_id)
        os.remove(pathname)

    def exists(self, item_id):
        pathname = os.path.join(self.path, item_id)
        return os.path.exists(pathname)

    def keys(self):
        return os.listdir(self.path)


Bucket = FileBucket