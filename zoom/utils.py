# -*- coding: utf-8 -*-

"""
    zoom.utils
"""

import collections
import configparser
import os
import string
import decimal
import datetime

chars = ''.join(map(chr, range(256)))
keep_these = string.ascii_letters + string.digits + '- '
delete_these = chars.translate(str.maketrans(chars, chars, keep_these))
allowed = str.maketrans(keep_these, keep_these, delete_these)


def kind(o):
    """
    returns a suitable table name for an object based on the object class
    """
    n = []
    for c in o.__class__.__name__:
        if c.isalpha() or c == '_':
            if c.isupper() and len(n):
                n.append('_')
            n.append(c.lower())
    return ''.join(n)


def id_for(*args):
    """
    Calculates a valid HTML tag id given an arbitrary string.

        >>> id_for('Test 123')
        'test-123'
        >>> id_for('New Record')
        'new-record'
        >>> id_for('New "special" Record')
        'new-special-record'
        >>> id_for("hi", "test")
        'hi~test'
        >>> id_for("hi test")
        'hi-test'
        >>> id_for("hi-test")
        'hi-test'
        >>> id_for(1234)
        '1234'
        >>> id_for('this %$&#@^is##-$&*!it')
        'this-is-it'

    """
    def id_(text):
        return str(text).strip().translate(allowed).lower().replace(' ', '-')

    return '~'.join([id_(arg) for arg in args])


def trim(text):
    """
        Remove the left most spaces for markdown

        >>> trim('remove right ')
        'remove right'

        >>> trim(' remove left')
        'remove left'

        >>> trim(' remove spaces \\n    from block\\n    of text ')
        'remove spaces\\n   from block\\n   of text'

    """
    n = 0
    for line in text.splitlines():
        if line.isspace():
            continue
        if line.startswith(' '):
            n = len(line) - len(line.lstrip())
            break
    if n:
        lines = []
        for line in text.splitlines():
            lines.append(line[n:].rstrip())
        return '\n'.join(lines)
    else:
        return text.strip()


class ItemList(list):
    """
    list of data items

    >>> items = ItemList()
    >>> items.append(['Joe', 12, 125])
    >>> items
    [['Joe', 12, 125]]
    >>> print(items)
    Column 0 Column 1 Column 2
    -------- -------- --------
    Joe            12      125

    >>> items.insert(0, ['Name', 'Score', 'Points'])
    >>> print(items)
    Name Score Points
    ---- ----- ------
    Joe     12    125

    >>> data = [
    ...     ['Joe', 12, 125],
    ...     ['Sally', 13, 1354],
    ... ]
    >>> items = ItemList(data)
    >>> print(items)
    Column 0 Column 1 Column 2
    -------- -------- --------
    Joe            12      125
    Sally          13    1,354

    >>> data = [
    ...     ['Joe', 12, 125],
    ...     ['Sally', 13, 135],
    ... ]
    >>> items = ItemList(data, labels=['Name', 'Score', 'Points'])
    >>> print(items)
    Name  Score Points
    ----- ----- ------
    Joe      12    125
    Sally    13    135


    """
    def __init__(self, *args, **kwargs):
        self.labels = kwargs.pop('labels', None)
        list.__init__(self, *args, **kwargs)

    def __str__(self):
        def is_numeric(value):
            return type(value) in [int, float, decimal.Decimal]

        def is_text(value):
            return type(value) in [str, bytes]

        def name_column(number):
            return 'Column {}'.format(number)

        def is_homogeneous(values):
            return any([
                len(values) <= 1,
                all(type(values[0]) == type(i) for i in values[1:]),
            ])

        def get_format(label, values):
            first_non_null = list(map(type, [a for a in values if a is not None]))[:1]
            if first_non_null:
                data_type = first_non_null[0]
                if data_type in [int, float, decimal.Decimal]:
                    return '{:{width},}'
                elif data_type in [datetime.date]:
                    return '{:%Y-%m-%d}'
                elif data_type in [datetime.datetime]:
                    return '{:%Y-%m-%d %H:%M:%S}'
                elif label in ['_id', 'userid']:
                    return '{:10}'
            return '{:<{width}}'

        if len(self) == 0:
            return ''

        num_columns = len(list(self[0]))
        columns = list(range(num_columns))

        # calculate labels
        if self.labels:
            labels = self.labels
            offset = 0
        else:
            if not all(is_text(label) for label in self[0]):
                labels = [name_column(i) for i in range(num_columns)]
                offset = 0
            else:
                labels = self[0]
                offset = 1

        # rows containing data
        rows = [list(row) for row in self[offset:]]

        # calculate formats
        formats = []
        for col in columns:
            values = [row[col] for row in rows]
            if is_homogeneous(values):
                formats.append(get_format(labels[col], values))
            else:
                formats.append('{}')

        # calulate formatted values
        formatted_values = [labels] + [
            [
                formats[col].format(row[col], width=0)
                for col in columns
            ] for row in rows
        ]

        # calculate column widths
        data_widths = {}
        for row in formatted_values:
            for col in columns:
                n = data_widths.get(col, 0)
                m = len(row[col])
                if n < m:
                    data_widths[col] = m

        label_format = '{:<{width}}'
        formatted_labels = [
                label_format.format(l, width=data_widths[i])
                for i, l in enumerate(labels)
                ]

        dashes = ['-' * data_widths[col] for col in columns]
        aligned_rows = [formatted_labels] + [dashes] + [
            [
                formats[col].format(row[col], width=data_widths[col])
                for col in columns
            ] for row in rows
        ]

        lines = [' '.join(row).rstrip() for row in aligned_rows]

        return '\n'.join(lines)


def parents(path):
    if not os.path.isdir(path):
        return parents(os.path.split(os.path.abspath(path))[0])
    parent = os.path.abspath(os.path.join(path, os.pardir))
    if path == parent:
        return []
    else:
        return [path] + parents(parent)


def locate_config(filename='zoom.conf', start='.'):
    for path in parents(start):
        pathname = os.path.join(path, filename)
        if os.path.exists(pathname):
            return pathname
    for path in parents(os.path.join(os.path.expanduser('~'))):
        pathname = os.path.join(path, filename)
        if os.path.exists(pathname):
            return pathname


class Config(object):

    def __init__(self, filename):
        self.config = configparser.ConfigParser()
        if not filename or not os.path.exists(filename):
            raise Exception('%s file missing' % filename)
        self.config.read(filename)

    def get(self, section, option, default=None):
        try:
            return self.config.get(section, option)
        except (configparser.NoOptionError, configparser.NoSectionError):
            if default is not None:
                return default
            raise


class OrderedSet(collections.MutableSet):
    """
    A Record with default values

    trimmed_rows = [row.strip() for row in aligned_rows]

        >>> s = OrderedSet('abracadaba')
        >>> t = OrderedSet('simsalabim')
        >>> print(s | t)
        OrderedSet(['a', 'b', 'r', 'c', 'd', 's', 'i', 'm', 'l'])
        >>> print(s & t)
        OrderedSet(['a', 'b'])
        >>> print(s - t)
        OrderedSet(['r', 'c', 'd'])

    credit: http://code.activestate.com/recipes/576694/
    Licensed under MIT License
    """

    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]         # sentinel node for doubly linked list
        self.map = {}                   # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        """test if item is present

            >>> s = OrderedSet([1, 2, 3])
            >>> 'c' in s
            False
            >>> 2 in s
            True
        """
        return key in self.map

    def add(self, key):
        """add an item

            >>> s = OrderedSet([1, 2, 3])
            >>> s.add(4)
            >>> s
            OrderedSet([1, 2, 3, 4])
        """
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def discard(self, key):
        """discard an item by key

            >>> s = OrderedSet([1, 2, 3])
            >>> s.discard(1)
            >>> s
            OrderedSet([2, 3])
        """
        if key in self.map:
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        """pop an item

            >>> s = OrderedSet([1, 2, 3])
            >>> s.pop(2)
            3
            >>> s
            OrderedSet([1, 2])
        """
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)
