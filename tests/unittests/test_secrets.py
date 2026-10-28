"""
    test secrets
"""

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# It's reasonable in this case.

import os
from unittest.mock import patch
import unittest

import zoom.encryption
import zoom.secrets
import zoom.database
import zoom.utils
from zoom.encryption import generate_key


class TestSecrets(unittest.TestCase):
    """test the Storage class"""

    def setUp(self):
        # run tests using in-memory SQLite
        self._db_patcher = patch.dict(os.environ, {'ZOOM_TEST_DATABASE_ENGINE': 'memory'})
        self._db_patcher.start()
        db = zoom.database.setup_test()
        zoom.system.site = self.site = zoom.utils.Bunch(db=db)
        self.store = zoom.store_of(zoom.secrets.Secret)
        self.store.zap()
        self.key_name = zoom.encryption.key_name + '_test'

    def tearDown(self):
        self._db_patcher.stop()
        self.store.delete(name='my-secret')

    def test_get_encryption_key(self):
        key = zoom.encryption.get_encryption_key(self.key_name)
        self.assertIsNone(key)

        key_name = self.key_name.upper()
        new_key = generate_key()
        os.environ.setdefault(key_name, new_key.decode())
        key = zoom.encryption.get_encryption_key(self.key_name)
        self.assertIsNotNone(key)

    def test_secrets_key_missing(self):
        os.environ.pop(self.key_name.upper(), None)
        key = zoom.encryption.get_encryption_key(self.key_name)
        self.assertIsNone(key)

    def test_connection(self):
        if os.environ.get('ZOOM_TEST_DATABASE_ENGINE') == 'memory':
            return
        tables = [row[0] for row in zoom.db('show tables')]
        self.assertGreaterEqual(len(tables), 9)
        for name in ('users', 'groups', 'audit_log'):
            self.assertIn(name, tables)

    def test_set_get_secret(self):
        key = generate_key()
        secrets = zoom.secrets.get_secrets(key, self.store)
        my_secret = 'my secret'
        my_encrypted_secret = secrets.set('my-secret', my_secret)
        self.assertNotEqual(my_secret, my_encrypted_secret)

        # print(zoom.secrets.get_secrets(key))
        # print(zoom.store_of(zoom.secrets.Secret))

        returned_value = secrets.get('my-secret')
        self.assertEqual(my_secret, returned_value)

    def test_get_secret(self):
        key = generate_key()
        secrets = zoom.secrets.get_secrets(key, self.store)
        my_secret = 'my secret'
        my_encrypted_secret = secrets.set('my-secret', my_secret)
        self.assertNotEqual(my_secret, my_encrypted_secret)

        returned_value = zoom.secrets.get_secret('my-secret', key, self.store)
        self.assertEqual(my_secret, returned_value)

    def test_keys(self):
        key = generate_key()
        secrets = zoom.secrets.get_secrets(key, self.store)
        my_secret = 'my secret'

        secrets.set('my-secret', my_secret)
        secrets.set('my-other-secret', my_secret)
        secrets.set('my-3rd-secret', my_secret)

        self.assertEqual(secrets.keys(), [
            'my-secret',
            'my-other-secret',
            'my-3rd-secret',
        ])

    def test_len_secrets(self):
        key = generate_key()
        secrets = zoom.secrets.get_secrets(key)
        my_secret = 'my secret'

        secrets.set('my-secret', my_secret)
        secrets.set('my-other-secret', my_secret)

        self.assertEqual(len(secrets), 2)

    def test_delete_secret(self):
        key = generate_key()
        secrets = zoom.secrets.get_secrets(key)
        my_secret = 'my secret'

        secrets.set('my-secret', my_secret)
        secrets.set('my-other-secret', my_secret)
        secrets.set('my-3rd-secret', my_secret)

        secrets.delete('my-other-secret')

        self.assertEqual(secrets.keys(), [
            'my-secret',
            'my-3rd-secret',
        ])

    def test_exists(self):
        key = generate_key()
        secrets = zoom.secrets.get_secrets(key, self.store)
        self.assertFalse(secrets.exists('missing'))
        secrets.set('my-secret', 'value')
        self.assertTrue(secrets.exists('my-secret'))

    def test_get_or_set(self):
        key = generate_key()
        secrets = zoom.secrets.get_secrets(key, self.store)
        default = 'default'
        self.assertEqual(secrets.get_or_set('x', default), default)
        self.assertEqual(secrets.get('x'), default)
        new_default = 'new'
        self.assertEqual(secrets.get_or_set('x', new_default), default)

    def test_update(self):
        key = generate_key()
        secrets = zoom.secrets.get_secrets(key, self.store)
        with self.assertRaises(KeyError):
            secrets.update('nope', 'v')
        secrets.set('a', 'v1')
        updated = secrets.update('a', 'v2')
        self.assertEqual(updated, 'v2')
        self.assertEqual(secrets.get('a'), 'v2')

    def test_rename(self):
        key = generate_key()
        secrets = zoom.secrets.get_secrets(key, self.store)
        with self.assertRaises(KeyError):
            secrets.rename('old', 'new')
        secrets.set('a', 'v')
        secrets.rename('a', 'b')
        self.assertIsNone(secrets.get('a'))
        self.assertEqual(secrets.get('b'), 'v')

    def test_pop(self):
        key = generate_key()
        secrets = zoom.secrets.get_secrets(key, self.store)
        self.assertIsNone(secrets.pop('x'))
        secrets.set('a', 'v')
        val = secrets.pop('a')
        self.assertEqual(val, 'v')
        self.assertIsNone(secrets.get('a'))

    def test_clear(self):
        key = generate_key()
        secrets = zoom.secrets.get_secrets(key, self.store)
        secrets.set('a', '1')
        secrets.set('b', '2')
        secrets.clear()
        self.assertEqual(len(secrets), 0)
