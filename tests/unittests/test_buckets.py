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
