# -*- coding: utf-8 -*-

"""
    zoom.jsonz

    JSON with extra converters
"""

import json
import datetime
from decimal import Decimal
from datetime import datetime, date
from sys import version_info


def _decode_datetime(text):
    return datetime.fromisoformat(text)

def _decode_datetime_pre_37(text):
    try:
        return datetime.strptime(text, '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        return datetime.strptime(text, '%Y-%m-%dT%H:%M:%S')

decode_datetime = _decode_datetime if version_info[:2] >= (3, 7) else _decode_datetime_pre_37

def loads(text):
    """load JSON from a string"""

    def dhandler(obj):
        """handles extra converters"""
        # pylint: disable=invalid-name
        if '__type__' in obj:
            t = obj['__type__']
            if t == 'datetime':
                return decode_datetime(obj['value'])
            elif t == 'date':
                return datetime.strptime(obj['value'], '%Y-%m-%d').date()
            elif t == 'decimal':
                return Decimal(str(obj['value']))
            elif t == 'bytes':
                return obj['value'].encode("utf-8")
        return obj

    return json.loads(text, object_hook=dhandler)


def dumps(data, *a, **k):
    """Convert to json with support for date and decimal types

    >>> dumps('test')
    '"test"'

    >>> loads(dumps('test'))
    'test'

    >>> loads(dumps(date(2015,1,1)))
    datetime.date(2015, 1, 1)

    >>> loads(dumps(Decimal('20.40')))
    Decimal('20.40')
    """

    def handler(obj):
        """handles extra converters"""
        if isinstance(obj, datetime):
            return dict(__type__='datetime', value=obj.isoformat())
        elif isinstance(obj, date):
            return dict(__type__='date', value=obj.isoformat())
        elif isinstance(obj, Decimal):
            return dict(__type__='decimal', value=str(obj))
        elif isinstance(obj, (bytes, bytearray)):
            return dict(__type__='bytes', value=obj.decode("utf-8"))
        else:
            msg = 'Object of type %s with value %s is not JSON serializable.'
            raise TypeError(msg % (type(obj), repr(obj)))

    return json.dumps(data, default=handler, *a, **k)
