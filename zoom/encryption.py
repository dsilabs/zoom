"""
    zoom encryption
"""

import os
import re
from cryptography.fernet import Fernet


key_name = 'zoom_encryption_key'
_SAFE_KEY_NAME = re.compile(r'^[A-Za-z0-9_]+$')


def generate_key():
    """Generate a new key"""
    return Fernet.generate_key()


def get_secrets_path():
    """Directory where secret key files are stored

    Defaults to ~/.zoom/secrets for local development. Production can set
    ZOOM_SECRETS_PATH=/run/secrets (or another service-managed path).
    """
    return os.path.expanduser(
        os.environ.get('ZOOM_SECRETS_PATH', '~/.zoom/secrets')
    )


def get_key_pathname(name=None):
    """Path to the encryption key file"""
    return os.path.join(get_secrets_path(), name or key_name)


def get_encryption_key(name=None):
    """Get site encryption key from file or environment"""
    name = name or key_name
    if not _SAFE_KEY_NAME.match(name):
        return None

    str_key = None
    pathname = get_key_pathname(name)
    if os.path.isfile(pathname):
        with open(pathname, 'r') as f:
            str_key = f.read().strip() or None

    if str_key is None:
        str_key = os.environ.get(name.upper())
        if str_key is not None:
            str_key = str_key.strip() or None

    return str_key.encode() if str_key is not None else None


class Encrypter:

    def __init__(self, key):
        if isinstance(key, str):
            key = key.encode()
        self.cipher = Fernet(key)

    def encrypt(self, value):
        encrypted_value = self.cipher.encrypt(value.encode('utf-8'))
        return encrypted_value

    def decrypt(self, encrypted_value):
        value = self.cipher.decrypt(encrypted_value).decode('utf-8')
        return value


def get_encrypter(key):
    return Encrypter(key)
