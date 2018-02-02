# -*- coding: utf-8 -*-

"""
zoom.cache - experimental
~~~~~~~~~~

Provides a cache mechanism that can be used to add automatic caching
to functions and methods.  Handy for caching generated pages.

Use as a function or method decorator.
"""

import logging
import time

import zoom
# from zoom.store import store
# from .store import Entity
# from .system import system
# from .helpers import message

__all__ = ['cached', 'clear_cache']


DEFAULT_CACHE_LIFE = 3600  # one hour expiry
debugging = False


class CacheEntry(zoom.store.Entity):
    pass


Entry = CacheEntry


def load(key):
    """Load content from cache"""
    entries = zoom.store.store_of(Entry)
    entry = entries.first(key=key)
    now = time.time()
    result = entry and entry.expiry > now and entry.value
    if result:
        logger = logging.getLogger(__name__)
        logger.debug('cache hit on %r', key)
    return result


def save(key, value, expire=DEFAULT_CACHE_LIFE):
    """Save content in cache"""
    logger = logging.getLogger(__name__)
    entries = zoom.store.store_of(Entry)
    now = time.time()
    entry = entries.first(key=key)
    if entry:
        entry.update(value=value, expiry=now + expire)
        logger.debug('overwrote expired cache entry %r', expire)
    else:
        entry = Entry(key=key, value=value, expiry=now + expire)
        logger.debug('new cache entry %r', entry.expiry)
    entries.put(entry)
    return value


def calc_key(method_name, *a):
    """Calculate a cache key"""
    return repr((zoom.system.request.app.name, method_name, a))


def clear_cache(method_name, *keys):
    """Clear all entries from cache"""
    entries = zoom.store.store_of(Entry)
    for entry in entries:
        entries.delete(entry)


def cached(*keys, **kv):
    """decorator that caches method results

    >>> bunch = zoom.utils.Bunch
    >>> key = 'x','abc'
    >>> db = zoom.database.setup_test('memory')
    >>> zoom.system.request = bunch(app=bunch(name='testapp'))
    >>> zoom.system.site = bunch(db=db)
    >>> class foo(object):
    ...     def __init__(self, value):
    ...         self.value = value
    ...     @cached(key)
    ...     def get_value(self, param=''):
    ...         return self.value + param
    >>> clear_cache(key)
    >>> a = foo('bar')
    >>> a.get_value()
    'bar'
    >>> a.value = 'bahr'
    >>> a.get_value()
    'bar'
    >>> clear_cache('get_value', key)
    >>> a.get_value()
    'bahr'
    """

    def cached_decorator(*args, **kwargs):
        func = keys[0]
        full_key = calc_key(func.__name__, args[1:], kwargs)
        return load(full_key) or save(full_key, func(*args, **kwargs))

    def cached_decorator_with_params(func):
        def wrapper(*args, **kwargs):
            expire = kv.pop('expire', DEFAULT_CACHE_LIFE)
            full_key = calc_key(func.__name__, keys, args[1:], kwargs)
            return load(full_key) or \
                save(full_key, func(*args, **kwargs), expire=expire)
        return wrapper

    if len(keys) == 1 and callable(keys[0]):
        # decorator applied without parameters
        return cached_decorator
    else:
        # decorator applied with parameters
        return cached_decorator_with_params
