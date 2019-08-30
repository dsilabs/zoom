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
