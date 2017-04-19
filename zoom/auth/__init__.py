"""
    zoom.auth

    TODO: add scrypt support when introduced into passlib (v1.7)
"""

__all__ = ['validate_password', 'hash_password']

import datetime

from passlib.context import CryptContext


def get_context():
    """create a password encryption context"""

    context = CryptContext(
        schemes=[
            "bcrypt_sha256",
        ],

        default="bcrypt_sha256",

        deprecated=[
        ],

        # vary rounds parameter randomly when creating new hashes...
        # all__vary_rounds=0.1,

        # logarithmic, 2**{rounds} and bound from 4 to 31
        bcrypt_sha256__rounds=14,
    )

    return context


def hash_password(password):
    """hash a password"""
    context = get_context()
    return context.encrypt(password)


def validate_password(password, stored_password_hash):
    """validate a password and return the best hash

    >>> hash = '$bcrypt-sha256$2a,14$q4iT8GFWNrwfYDIMKaYI0e$KVxn8PWpzKbOgE/qfwG.IVhRIx.Pma6'
    >>> validate_password('admin', hash)
    (True, None)

    >>> validate_password('admin1', hash)
    (False, None)

    >>> new_hash = hash_password('adminpw')
    >>> validate_password('adminpw', new_hash)
    (True, None)

    Validates the supplied password to see if it matches the stored password
    based one of the accepted algorythms and also returns a hash based on the
    best algorythm that is currently supported.  This allows passwords stored
    with older algorythms to be accepted while providing the ability to
    contantly upgrade algorythms as they improve.
    """
    context = get_context()
    return context.verify_and_update(password, stored_password_hash)
