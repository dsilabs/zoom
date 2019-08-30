<<<<<<< HEAD
"""Unit tests against buckets."""
import unittest
import uuid

from zoom.buckets import Bucket, FileBackend, DatabaseBackend

class BucketTestSuite(unittest.TestCase):

	def test_construction(self):
		fs_bucket_path = '/tmp/_test_bucket_' + uuid.uuid4().hex

		# Test deprecated behaviour.
		with self.assertLogs('zoom.buckets', level='WARNING') as logs:
			bucket = Bucket(fs_bucket_path)
			assert 'deprecated' in ''.join(logs.output), 'Deprecation warning missing'
			assert isinstance(bucket.backend, FileBackend), 'Bad backend selected'

		# Test each backend.
		def test_bucket_backend(bucket, BackendCls):
			msg = lambda m: m + ': ' + str(BackendCls)
			assert isinstance(bucket.backend, BackendCls), msg('Bad backend selected')

			item_id = bucket.put(b'data')
			assert len(item_id) == 32, msg('Invalid ID format')
			assert bucket.get(item_id) == b'data', msg('Invalid data returned')
			assert bucket.exists(item_id), msg('Invalid existance result')
			keys = bucket.keys()
			assert len(keys) == 1 and keys[0] == item_id, msg('Invalid keys: ' + str(keys))

			bucket.delete(item_id)
			assert not bucket.keys(), msg('Invalid empty key set')

		# Run suite on fs bucket.
		test_bucket_backend(Bucket(path=fs_bucket_path), FileBackend)

		# Ensure database backend is selected.
		assert isinstance(Bucket(name='db_backend').backend, DatabaseBackend), 'Bad backend selected'
		
		# Run suite on db bucket.
		bucket = Bucket(backend=DatabaseBackend(name='test_bucket', test_db=True))
		test_bucket_backend(bucket, DatabaseBackend)
=======
"""
    test buckets
"""

import os
import unittest

import zoom
from zoom.buckets import Bucket


class TestFileBucket(unittest.TestCase):
    """test file buckets module"""

    def clear(self):
        bucket = Bucket(self.path, self.ids.pop)
        for item_id in bucket.keys():
            bucket.delete(item_id)

    def setUp(self):
        self.site = zoom.sites.Site()
        self.path = os.path.join(self.site.data_path, 'buckets')
        self.ids = ['id_%04d' % (9-i) for i in range(10)]
        self.clear()

    def tearDown(self):
        self.clear()

    def test_put_get(self):
        bucket = Bucket(self.path, self.ids.pop)
        item_id = bucket.put(b'some data')
        self.assertEqual(item_id, 'id_0000')
        self.assertEqual(bucket.get(item_id), b'some data')

    def test_item_exists(self):
        bucket = Bucket(self.path, self.ids.pop)
        item_id = bucket.put(b'some data')
        self.assertEqual(item_id, 'id_0000')
        self.assertEqual(bucket.exists(item_id), True)

    def test_keys(self):
        bucket = Bucket(self.path, self.ids.pop)
        self.assertEqual(bucket.put(b'some data'), 'id_0000')
        self.assertEqual(bucket.put(b'some more data'), 'id_0001')
        self.assertEqual(
            sorted(bucket.keys()),
            ['id_0000', 'id_0001']
        )

    def test_delete(self):
        bucket = Bucket(self.path, self.ids.pop)
        self.assertEqual(bucket.put(b'some data'), 'id_0000')
        self.assertEqual(bucket.put(b'some more data'), 'id_0001')
        self.assertEqual(
            sorted(bucket.keys()),
            ['id_0000', 'id_0001']
        )
        for item_id in bucket.keys():
            bucket.delete(item_id)
        self.assertEqual(
            sorted(bucket.keys()),
            []
        )
>>>>>>> master
