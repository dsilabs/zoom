"""
    zoom.auth.handlers

    Zoom password hash support - passlib

    PEPPER: bcrypt(b64encode(new_hmac(self.pepper(), secret, sha256).digest()))
        b64encode to avoid null bytes!
"""

import re
from base64 import b64encode
from hashlib import sha1, sha256

from passlib.handlers.mysql import mysql41
from passlib.utils.compat import u, str_to_uascii, byte_elem_value
from passlib.handlers.bcrypt import bcrypt_sha256

# local
__all__ = [
    "DataZoomerSaltedHash",
]

# DataZoomer weak-salt charset
SALT_CHARS = '0123456789- :'

# salted hashes
class DataZoomerSaltedHash(mysql41):
    """base class providing common code for DataZoomer hashes"""
    name = "datazoomer_weak_salt"

    def _calc_checksum(self, secret):
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        if not hasattr(self, "salt_fn"):
            msg = "No salt function specified for DataZoomerSaltedHash"
            raise RuntimeError(msg)
        salt = callable(self.salt_fn) and self.salt_fn() or self.salt_fn
        return str_to_uascii(
            sha1(
                sha1(salt.encode("ascii") + secret).digest()
            ).hexdigest()
        ).upper()


# legacy support (bcrypt our legacy hashes within the database)
class BcryptDataZoomerSaltedHash(bcrypt_sha256):
    """base class providing common code for DataZoomer hashes"""
    name = "bcrypt_sha256_dz_weak_salt"
    prefix = u('$bcrypt-sha256-dz$')
    _hash_re = re.compile(r"""
        ^
        [$]bcrypt-sha256-dz
        [$](?P<variant>[a-z0-9]+)
        ,(?P<rounds>\d{1,2})
        [$](?P<salt>[^$]{22})
        ([$](?P<digest>.{31}))?
        $
        """, re.X)

    def _calc_checksum(self, secret):

        if isinstance(secret, unicode):
            secret = secret.encode("utf-8")

        if not hasattr(self, "salt_fn"):
            msg = "No salt function specified for DataZoomerSaltedHash"
            raise RuntimeError(msg)

        weak_dz_salt = \
            callable(self.salt_fn) and self.salt_fn() or self.salt_fn

        dz_hash = (
            '*' + 
            str_to_uascii(
                sha1(
                    sha1(
                        weak_dz_salt.encode("ascii") + secret
                    ).digest()
                ).hexdigest()
            ).upper()
        )

        # NOTE: can't use digest directly, since bcrypt stops at first NULL.
        # NOTE: bcrypt doesn't fully mix entropy for bytes 55-72 of password
        #       (XXX: citation needed), so we don't want key to be > 55 bytes.
        #       thus, have to use base64 (44 bytes) rather than hex (64 bytes).
        key = b64encode(sha256(dz_hash).digest())
        return self._calc_checksum_backend(key)


class BcryptMySQL41(bcrypt_sha256):
    """bcrypts the legacy MySQL41 hash"""
    name = "bcrypt_sha256_mysql41"
    prefix = u('$bcrypt-sha256-mysql41$')
    _hash_re = re.compile(r"""
        ^
        [$]bcrypt-sha256-mysql41
        [$](?P<variant>[a-z0-9]+)
        ,(?P<rounds>\d{1,2})
        [$](?P<salt>[^$]{22})
        ([$](?P<digest>.{31}))?
        $
        """, re.X)

    def _calc_checksum(self, secret):
        # NOTE: this bypasses bcrypt's _calc_checksum,
        #       so has to take care of all it's issues, such as secret encoding.
        if isinstance(secret, str):
            secret = secret.encode("utf-8")

        # generate the mysql41 hash first (as it would be in the db
        mysql41_hash = (
            '*' + 
            str_to_uascii(sha1(sha1(secret).digest()).hexdigest()).upper()
        )

        # NOTE: can't use digest directly, since bcrypt stops at first NULL.
        # NOTE: bcrypt doesn't fully mix entropy for bytes 55-72 of password
        #       (XXX: citation needed), so we don't want key to be > 55 bytes.
        #       thus, have to use base64 (44 bytes) rather than hex (64 bytes).
        key = b64encode(sha256(mysql41_hash).digest())
        return self._calc_checksum_backend(key)


class BcryptMySQL323(bcrypt_sha256):
    """bcrypts the legacy MySQL323 hash"""
    name = "bcrypt_sha256_mysql323"
    prefix = u('$bcrypt-sha256-mysql323$')
    _hash_re = re.compile(r"""
        ^
        [$]bcrypt-sha256-mysql323
        [$](?P<variant>[a-z0-9]+)
        ,(?P<rounds>\d{1,2})
        [$](?P<salt>[^$]{22})
        ([$](?P<digest>.{31}))?
        $
        """, re.X)

    def _calc_checksum(self, secret):
        # NOTE: this bypasses bcrypt's _calc_checksum,
        #       so has to take care of all it's issues, such as secret
        #       encoding.
        if isinstance(secret, str):
            secret = secret.encode("utf-8")

        # generate the mysql323 hash first (as it would be in the db
        MASK_32 = 0xffffffff
        MASK_31 = 0x7fffffff
        WHITE = b' \t'

        nr1 = 0x50305735
        nr2 = 0x12345671
        add = 7
        for c in secret:
            if c in WHITE:
                continue
            tmp = byte_elem_value(c)
            nr1 ^= ((((nr1 & 63)+add)*tmp) + (nr1 << 8)) & MASK_32
            nr2 = (nr2+((nr2 << 8) ^ nr1)) & MASK_32
            add = (add+tmp) & MASK_32
        mysql323_hash = u("%08x%08x") % (nr1 & MASK_31, nr2 & MASK_31)

        # NOTE: can't use digest directly, since bcrypt stops at first NULL.
        # NOTE: bcrypt doesn't fully mix entropy for bytes 55-72 of password
        #       (XXX: citation needed), so we don't want key to be > 55 bytes.
        #       thus, have to use base64 (44 bytes) rather than hex (64 bytes).
        key = b64encode(sha256(mysql323_hash).digest())
        return self._calc_checksum_backend(key)
