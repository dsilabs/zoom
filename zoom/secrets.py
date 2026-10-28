"""
    secrets
"""

import os
import zoom
from zoom.encryption import get_encrypter, get_encryption_key
from zoom.store import EntityStore, store_of


class Secret(zoom.store.Entity):

    @property
    def key(self):
        return self.name

    @property
    def url(self):
        return f'/secrets/{self.key}'

    @property
    def link(self):
        return zoom.link_to(self.name, self.url)


class SecretsKeyMissingException(Exception): pass


def get_secrets_encrypter(key=None):
    key = key or get_encryption_key()
    if not key:
        raise SecretsKeyMissingException('Secrets encryption key missing')
    return get_encrypter(key)


class Secrets:

    def __init__(self, key, storage=None):
        if storage is None:
            storage = get_secrets_store()
        elif not isinstance(storage, SecretEntityStore):
            storage = SecretEntityStore(storage.db, Secret)
        storage.set_encrypter(get_secrets_encrypter(key))
        self.storage = storage

    def set(self, name, value, expiry=None):
        record = Secret(
            name=name,
            value=value,
            expiry=expiry
        )
        self.storage.put(record)
        return record.value

    def get(self, name):
        record = self.storage.first(name=name)
        if record:
            return record.value

    def delete(self, name):
        self.storage.delete(name=name)

    def keys(self):
        return list(s.name for s in self.storage)

    def list(self):
        return list(self.storage)

    def first(self, name):
        return self.storage.first(name=name)

    def exists(self, name):
        return self.storage.first(name=name) is not None

    def get_or_set(self, name, default_value, expiry=None):
        record = self.storage.first(name=name)
        if record:
            return record.value
        self.set(name, default_value, expiry)
        return default_value

    def update(self, name, value):
        record = self.storage.first(name=name)
        if not record:
            raise KeyError(name)
        self.delete(name)
        self.set(name, value)
        return value

    def rename(self, old_name, new_name):
        record = self.storage.first(name=old_name)
        if not record:
            raise KeyError(old_name)
        record.name = new_name
        self.storage.put(record)

    def pop(self, name):
        value = self.get(name)
        if value is None:
            return None
        self.delete(name)
        return value

    def clear(self):
        for secret in list(self.storage):
            self.delete(secret.name)

    def __iter__(self):
        return self.storage.__iter__()

    def __len__(self):
        return len(self.storage)

    def __str__(self):

        return '\nSecrets\n--------------\n' + ''.join(
            f'{secret.name}'
            for secret in self.list()
        )

def get_secrets(key=None, storage=None):
    return Secrets(key, storage)


def get_secret(name, key=None, storage=None):
    return get_secrets(key, storage).get(name)


def set_secret(name, value, key=None, storage=None):
    return get_secrets(key, storage).set(name, value)


class SecretEntityStore(EntityStore):

    def __init__(self, *args, **kwargs):
        self.encrypter = None
        super().__init__(*args, **kwargs)

    def set_encrypter(self, encrypter):
        self.encrypter = encrypter

    def get_encrypter(self):
        if self.encrypter is None:
            self.encrypter = get_secrets_encrypter()
        return self.encrypter

    def put(self, *args, **kwargs):
        return super().put(*args, **kwargs)

    def _get_value(self, record):
        if record is None:
            return None
        if isinstance(record, dict):
            return record.get('value')
        return record.value

    def _set_value(self, record, value):
        if record is None:
            return
        if isinstance(record, dict):
            record['value'] = value
        else:
            record.value = value

    def _decrypt_record(self, record):
        value = self._get_value(record)
        if record and isinstance(value, (bytes, bytearray)):
            self._set_value(record, self.get_encrypter().decrypt(value))
        return record

    def _decrypt_records(self, records):
        if isinstance(records, list):
            for idx in range(len(records)):
                self._decrypt_record(records[idx])
            if hasattr(records, '_n'):
                records._n = 0
            return records
        return self._decrypt_record(records)

    def get(self, keys):
        records = super().get(keys)
        return self._decrypt_records(records)

    def all(self):
        records = super().all()
        return self._decrypt_records(records)

    def first(self, **kv):
        record = super().first(**kv)
        return self._decrypt_record(record)

    def before_insert(self, record):
        value = self._get_value(record)
        if value is not None and not isinstance(value, (bytes, bytearray)):
            self._set_value(record, self.get_encrypter().encrypt(value))

    def before_update(self, record):
        value = self._get_value(record)
        if value is not None and not isinstance(value, (bytes, bytearray)):
            self._set_value(record, self.get_encrypter().encrypt(value))


def get_secrets_store():
    db = zoom.get_db()
    return SecretEntityStore(db, Secret)
