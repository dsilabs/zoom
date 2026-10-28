"""
    test encryption
"""

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# It's reasonable in this case.

import os
import tempfile
import unittest
from unittest.mock import patch

import zoom.encryption
from zoom.encryption import (
    generate_key,
    get_encryption_key,
    get_secrets_path,
    key_name,
)


class TestEncryption(unittest.TestCase):
    """test encryption helpers"""

    def setUp(self):
        self.key = generate_key()
        self.encrypter = zoom.encryption.get_encrypter(self.key)

    def test_generate_key(self):
        key = generate_key()
        self.assertEqual(type(key), type(b''))
        self.assertEqual(len(key), 44)

    def test_encrypt_decrypt(self):
        my_sensitive_data = 'my data'
        my_encrypted_sensitive_data = self.encrypter.encrypt(my_sensitive_data)
        self.assertNotEqual(my_sensitive_data, my_encrypted_sensitive_data)
        self.assertEqual(
            my_sensitive_data,
            self.encrypter.decrypt(my_encrypted_sensitive_data)
        )

    def test_encrypter_accepts_str_key(self):
        key = generate_key().decode()
        encrypter = zoom.encryption.get_encrypter(key)
        self.assertEqual(encrypter.decrypt(encrypter.encrypt('x')), 'x')

    def test_get_encryption_key_from_env(self):
        name = key_name + '_envtest'
        env_name = name.upper()
        value = generate_key().decode()
        with patch.dict(os.environ, {env_name: value + '\n'}):
            key = get_encryption_key(name)
        self.assertEqual(key, value.encode())

    def test_get_encryption_key_from_file(self):
        name = key_name + '_filetest'
        value = generate_key().decode()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, name)
            with open(path, 'w') as f:
                f.write(value + '\n')
            with patch.dict(os.environ, {'ZOOM_SECRETS_PATH': tmpdir}, clear=False):
                os.environ.pop(name.upper(), None)
                key = get_encryption_key(name)
        self.assertEqual(key, value.encode())

    def test_get_encryption_key_rejects_unsafe_name(self):
        self.assertIsNone(get_encryption_key('../etc/passwd'))
        self.assertIsNone(get_encryption_key('bad name'))

    def test_get_encryption_key_missing(self):
        name = key_name + '_missing'
        with patch.dict(os.environ, {'ZOOM_SECRETS_PATH': '/no/such/path'}, clear=False):
            os.environ.pop(name.upper(), None)
            self.assertIsNone(get_encryption_key(name))

    def test_default_secrets_path_is_user_home(self):
        env = {k: v for k, v in os.environ.items() if k != 'ZOOM_SECRETS_PATH'}
        with patch.dict(os.environ, env, clear=True):
            path = get_secrets_path()
        self.assertEqual(path, os.path.expanduser('~/.zoom/secrets'))

    def test_secrets_path_expands_user(self):
        with patch.dict(os.environ, {'ZOOM_SECRETS_PATH': '~/custom-secrets'}):
            self.assertEqual(
                get_secrets_path(),
                os.path.expanduser('~/custom-secrets'),
            )
