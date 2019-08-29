# coding: utf-8
"""Store and retrieve blobs of data.

>>> from zoom.buckets import Bucket, DatabaseBackend
>>> bucket = Bucket(backend=DatabaseBackend('test', test_db=True))
>>> item_id = bucket.put(b'some data')
>>> len(item_id)
32
>>> bucket.get(item_id)
b'some data'
>>> bucket.exists(item_id)
True
>>> bucket.delete(item_id)
>>> bucket.exists(item_id)
False

>>> fake_id = 'c0f111b46b114ec2966ce34067cd9012'
>>> bucket.exists(fake_id)
False
>>> bucket.get(fake_id)
Traceback (most recent call last):
    File "/usr/lib/python3.6/doctest.py", line 1330, in __run
        compileflags, 1), test.globs)
    File "<doctest buckets.py[11]>", line 1, in <module>
        bucket.get(fake_id)
    File "/home/robin_m_saxifrage/core-dev/zoom/zoom/buckets.py", line 141, in get
        raise KeyError(str(blob_id))
KeyError: 'c0f111b46b114ec2966ce34067cd9012'

"""

import os
import logging

from uuid import UUID, uuid4

from zoom.tools import get_calling_app, zoompath
from zoom.database import DatabaseException, database as get_database
from zoom.context import context

# Define constants.
# pylint: disable=line-too-long
POSITIONAL_PATH_DEPR_WARNING = "Creating a Bucket with Bucket('<path>') is deprecated, use Bucket() / Bucket(name='<name>') to use the new database backend, or Bucket(path='<path>') to use the old filesystem one."
# pylint: enable=line-too-long
SETUP_SQL_REL_PATH = 'zoom/sql/{dialect}/create_bucket_tables.sql'

# Create a logger.
log = logging.getLogger(__name__)

# Define the bucket API.
class Bucket:
    """Buckets can store and retreive blobs of binary data. This is useful for
    storing images or files as attachments; any time you want to put binary
    data somewhere and retreive it later. 
    
    Specifically, the ID returned by `put` should generally be associated with
    other entities in the system.
    
    Buckets can be powered by two different backends; database based (default,
    canonical), and filesystem based (useful in certain circumstances). You
    can also implement custom backends as subclasses of the `BucketBackend`
    class."""

    def __init__(self, *args, path=None, name=None, backend=None, **kwargs):
        """Construct a bucket."""
        # For backwards compatability, we interpret a single positional as
        # a filesystem path, but supply a deprecation warning.
        if args:
            # Ensure the arguments are sane.
            if len(args) != 1:
                raise ValueError('Invalid bucket constructor.')
            # Take the path and warn.
            path = args[0]
            log.warn(POSITIONAL_PATH_DEPR_WARNING)
        # Validate kwarguments.
        if kwargs:
            # The id_factory keyword argument is no longer supported as this
            # collection is now stored in a table and therefore strictly schemad.
            if 'id_factory' in kwargs:
                raise ValueError('id_factory is no longer supported.')
            raise ValueError('Invalid kwargs supplied.')
        
        # Resolve the backend.
        self.backend = self._get_backend(path, name, backend)

    def _get_backend(self, path, name, backend):
        """Return an instantiated backend for this bucket to use."""
        if backend:
            # Ensure no other arugments were supplied.
            if path or name:
                raise ValueError("Don't specify path or name with a backend")
            # Use the supplied custom backend.
            return backend
        if path:
            # A path was specified, use the old file-system backend.
            return FileBackend(path)
        else:
            # Use the default database backend.
            if not name:
                # Name this bucket after its owner app.
                name = get_calling_app()
                if not name:
                    raise ValueError('Supply a name')
                name += '_app_bucket'
            return DatabaseBackend(name)

    def _format_blob_id(self, blob_id):
        """Ensure a supplied blob ID is valid and return it as a UUID string
        without dashes, or raise a `ValueError`."""
        # Handle UUIDs.
        if isinstance(blob_id, UUID):
            return blob_id.hex
        # Handle strings with validation.
        if isinstance(blob_id, str):
            try:
                return UUID(blob_id).hex
            except: pass

        # Handle failure.
        raise ValueError('Invalid blob_id: ' + str(blob_id))

    def put(self, blob):
        """Put a blob in this bucket. Returns the ID with which it can be
        retrieved."""
        # Create the ID.
        blob_id = self._format_blob_id(uuid4())

        # Use the backend to create the blob and return the reference ID.
        self.backend.write_blob(blob_id, blob)
        return blob_id

    def get(self, blob_id, default=None):
        """Retrieve the blob associated to the given ID from this bucket will
        raise a `KeyError` if the key is missing unless a `default` is
        supplied."""
        # Canonicalize the ID, asserting it's valid.
        blob_id = self._format_blob_id(blob_id)

        # Retrieve the blob from the backend if it exists.
        blob = self.backend.read_blob(blob_id)

        # Handle the blob not existing or return it.
        if blob is None:
            if default:
                return default
            raise KeyError(str(blob_id))
        return blob

    def delete(self, blob_id):
        """Delete the blob with the given ID or raise a `KeyError` if it
        doesn't exist."""
        # Canonicalize the ID, asserting it's valid.
        blob_id = self._format_blob_id(blob_id)

        # Ensure it exists. Hopefully this check will make app bugs more
        # apparent.
        if not self.backend.blob_exists(blob_id):
            raise KeyError(str(blob_id))

        self.backend.delete_blob(blob_id)

    def exists(self, blob_id):
        """Return whether or not this bucket contains a blob with the given
        ID."""
        # Canonicalize the ID, asserting it's valid.
        blob_id = self._format_blob_id(blob_id)

        return self.backend.blob_exists(blob_id)

    def keys(self):
        """Return the IDs of all blobs in this bucket."""
        # Return all IDs provided by the backend, canonicalized.
        return list(filter(
            self._format_blob_id, self.backend.get_blob_ids()
        ))

# Define the bucket backend super class and stock implementations.
class BucketBackend:
    """The base class of a bucket backend. Inheritors must implement every
    method."""

    def write_blob(self, blob_id, data):
        """Write the given data blob associated to the given ID or raise a nice
        exception."""
        raise NotImplementedError()

    def read_blob(self, blob_id):
        """Load and return the given data blob, or `None` if it doesn't
        exist."""
        raise NotImplementedError()

    def delete_blob(self, blob_id):
        """Practically delete the given data blob."""
        raise NotImplementedError()
    
    def blob_exists(self, blob_id):
        """Return whether or not this backend contains a blob with the given
        ID."""
        raise NotImplementedError()

    def get_blob_ids(self):
        """Return all blob IDs in this backend."""
        return NotImplementedError()

class DatabaseBackend(BucketBackend):
    """DatabaseBackend stores blobs in the database."""

    def __init__(self, name, test_db=False):
        """Create a new database backend. This includes creating tables if they
        don't yet exist, although that work is deferred until use."""
        self.name = name
        self.bucket_id = None

        self._db = None
        if test_db:
            self._db = get_database('sqlite3', database=':memory:')
        self._initialized = False
        
    def _initialize(self, db):
        """Initialize the nessesary tables if they don't already exist."""
        # Manage once-lock.
        if self._initialized:
            return
        self._initialized = True

        # Check whether or not we need to create tables.
        db_exists = True
        try:
            db('select id from buckets limit 1;')
        except DatabaseException as ex:
            log.debug('No tables yet.')
            log.debug('%s', str(ex))
            db_exists = False
        
        # Create the database if it doesn't exist.
        if not db_exists:
            # Resolve the path to the SQL file and read it.
            setup_sql_path = zoompath(SETUP_SQL_REL_PATH.format(
                dialect=db.dialect
            ))
            with open(setup_sql_path) as sql_file:
                setup_sql = sql_file.read()

            # Execute the setup.
            for sql_stmt in setup_sql.split(';'):
                try:
                    db(sql_stmt)
                except DatabaseException as ex:
                    log.debug(str(ex))
                    raise DatabaseException(
                        "Can't create bucket tables (is this a permissions "
                        'error)?'
                    )

        # Retrieve the in-database ID for this bucket.
        existing_bucket = db('''
            select id from buckets where name = %s;
        ''', self.name,)
        if len(existing_bucket):
            self.bucket_id = existing_bucket.first()[0]
            log.debug('loaded bucket: %s', self.bucket_id)
        else:
            # We need to create a new bucket.
            db('''
                insert into buckets (name) values (%s);
            ''', self.name,)
            created_id = db.lastrowid

            log.debug('created bucket: %s', created_id)
            self.bucket_id = created_id

    def _get_db(self):
        """A DB access point to allow changes to access strategy later. Also
        handles invoking database initialization if needed."""
        if context.site:
            db = context.site.db
        elif self._db:
            db = self._db
        else:
            raise RuntimeError('No accessible database.')
        self._initialize(db)
        return db

    def write_blob(self, blob_id, blob):
        """Store the given blob in the database."""
        db = self._get_db()

        # Write the blob.
        db('''
            insert into bucket_blobs (id, bucket_id, data) values (%s, %s, %s);
        ''', blob_id, self.bucket_id, blob)

    def read_blob(self, blob_id):
        """Load and return the given blob from the database."""
        db = self._get_db()

        # Read the blob and return its contents or None.
        result = db('''
            select data from bucket_blobs where id = %s and bucket_id = %s;
        ''', blob_id, self.bucket_id).first()
        if result:
            return result[0]
        return None

    def delete_blob(self, blob_id):
        """Delete the given blob from the database."""
        db = self._get_db()

        # Delete the blob.
        db('''
            delete from bucket_blobs where id = %s and bucket_id = %s;
        ''', blob_id, self.bucket_id)

    def blob_exists(self, blob_id):
        """Return whether or not the given blob exists."""
        db = self._get_db()

        # Readback the ID.
        result = db('''
            select id from bucket_blobs where id = %s and bucket_id = %s;
        ''', blob_id, self.bucket_id)
        return bool(list(*result))

    def get_blob_ids(self):
        """Return all blob IDs in this bucket."""
        db = self._get_db()

        # Load all rows associated with this bucket and return their
        # de-referenced IDs.
        rows = db('''
            select id from bucket_blobs where bucket_id = %s;
        ''', self.bucket_id)
        return list(*filter(lambda r: r[0], rows))

class FileBackend(BucketBackend):
    """FileBackend stores directly into a folder on the drive of the web server
    where it has sufficient permissions to do so. This is a potential attack
    area so be careful to take the appropriate precautions.

    The location of the buckets is determined by `[data]` path setting in the
    `site.ini` configuration file."""

    def __init__(self, path):
        """Create a new file backend at the given backend."""
        # Canonicalize the path and create the directory if it doesn't exist.
        self.path = os.path.realpath(path)
        if not os.path.isdir(path):
            os.makedirs(path)

    def write_blob(self, blob_id, blob):
        """Store the blob in a file with the ID as the name."""
        # Resolve the destination path and assert it doesn't exist.
        filepath = os.path.join(self.path, blob_id)
        if os.path.exists(filepath):
            raise ValueError('Duplicate blob_id: ' + blob_id)

        # Write the blob.
        with open(filepath, 'wb') as dest_file:
            dest_file.write(blob)

    def read_blob(self, blob_id):
        """Load the blob file with the given ID."""
        # Resolve the target path and handle it not existing.
        filepath = os.path.join(self.path, blob_id)
        if not os.path.exists(filepath):
            return None

        # Load and return the blob.
        with open(filepath, 'rb') as src_file:
            return src_file.read()

    def delete_blob(self, blob_id):
        """Delete the blob with the given ID."""
        os.remove(os.path.join(self.path, blob_id))

    def blob_exists(self, blob_id):
        """Return whether or not the blob with the given ID exists."""
        return os.path.exists(os.path.join(self.path, blob_id))

    def get_blob_ids(self):
        """Return the name of every file in the data directory."""
        return os.listdir(self.path)
