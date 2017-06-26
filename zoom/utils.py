# -*- coding: utf-8 -*-

"""
    zoom.utils
"""

import collections
import configparser
import logging
import os
import string
import decimal
import datetime
import zoom.jsonz as json

chars = ''.join(map(chr, range(256)))
keep_these = string.ascii_letters + string.digits + '- '
delete_these = chars.translate(str.maketrans(chars, chars, keep_these))
allowed = str.maketrans(keep_these, keep_these, delete_these)


def pretty(obj):
    """return an object in a pretty form

    >>> obj = dict(name='Joe', age=25)
    >>> pretty(obj)
    '{\\n  "age": 25,\\n  "name": "Joe"\\n}'
    """
    try:
        return json.dumps(obj, indent=2, sort_keys=True)
    except TypeError:
        if type(obj) == dict:
            return '{\n%s\n}' % '\n'.join([
                '  {!r} {}: {!r}'.format(key, '.' * (15 - len(key)), value)
                for key, value in sorted(obj.items())
            ])
        elif hasattr(obj, '__dict__'):
            return '<%s \n%s\n>' % (obj.__class__.__name__, '\n'.join([
                '  {} {}: {!r}'.format(key, '.' * (15 - len(key)), value)
                for key, value in sorted(obj.__dict__.items())
            ]))
        else:
            return repr(obj)


def pp(obj):
    """pretty print an object

    >>> obj = dict(name='Joe', age=25)

    >>> pp(obj)
    {
      "age": 25,
      "name": "Joe"
    }

    """
    # pylint: disable=C0103
    print(pretty(obj))


def dictify(item):
    """prepare an object for transmission by marshalling it's members

    Marshals only members that json can handle.
    """
    # pylint: disable=W0703

    result = {}
    for k, v in item.__dict__.items():
        try:
            json.dumps(v)
        except Exception:
            pass
        else:
            result[k] = v
    return result


def sorted_column_names(names):
    def looks_like_an_id(text):
        return text.endswith('_id')

    id_names = sorted(name for name in names if looks_like_an_id(name))
    special_names = id_names + [
        'id', 'userid', 'groupid', 'key',
        'name', 'title', 'description',
        'first_name', 'middle_name', 'last_name', 'fname', 'lname'
    ]
    result = []
    for name in special_names:
        if name in names:
            result.append(name)
    for name in sorted(names, key=lambda a: (len(a), a)):
        if name not in result:
            result.append(name)
    return result


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


def name_for(text):
    """Calculates a valid HTML field name given an arbitrary string."""
    return text.replace('*', '').replace(' ', '_').strip().lower()


def trim(text):
    """Remove the left most spaces for markdown

    >>> trim('remove right ')
    'remove right'

    >>> trim(' remove left')
    'remove left'

    >>> print(trim(' remove spaces\\n    from block\\n    of text'))
    remove spaces
       from block
       of text

    >>> print(trim('    remove spaces\\n  from block\\n  of text'))
      remove spaces
    from block
    of text

    >>> print(trim('\\n  remove spaces\\n    from block\\n  of text'))
    <BLANKLINE>
    remove spaces
      from block
    of text

    >>> text = '\\nremove spaces  \\n    from block\\nof text'
    >>> print('\\n'.join(repr(t) for t in trim(text).splitlines()))
    'remove spaces  '
    '    from block'
    'of text'

    """
    trim_size = None
    lines = text.splitlines()
    for line in lines:
        if line.isspace():
            continue
        n = len(line) - len(line.lstrip())
        trim_size = trim_size is not None and min([trim_size, n]) or n
    if trim_size:
        result = []
        for line in lines:
            result.append(line[trim_size:])
        return '\n'.join(result)
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
            first_non_null = list(
                map(type, [a for a in values if a is not None])
            )[:1]
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

        sorted_names = sorted_column_names(labels)

        if not self.labels:
            columns = sorted(columns, key=lambda a: sorted_names.index(labels[a]))
        dashes = ['-' * data_widths[col] for col in columns]
        sorted_labels = [formatted_labels[col] for col in columns]

        aligned_rows = [sorted_labels] + [dashes] + [
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


class Bunch(object):
    """a handy bunch of variables"""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class Storage(dict):
    """
    A Storage object is like a dictionary except `obj.foo` can be used
    in addition to `obj['foo']`.

        >>> o = Storage(a=1)
        >>> o.a
        1
        >>> o['a']
        1
        >>> o.a = 2
        >>> o['a']
        2
        >>> del o.a
        >>> o.a

    """
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as k:
            return None

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k:
            raise AttributeError(k)

    def __repr__(self):
        return '<Storage ' + dict.__repr__(self) + '>'


def get_attributes(obj):
    def properties(obj):
        if type(obj) == dict:
            return []
        items = list(obj.__class__.__dict__.items())
        return [k for k, v in items if type(v) == property]
    names = list(obj.keys()) + properties(obj)
    return sorted_column_names(names)


class Record(Storage):
    """
    A dict with attribute access to items, attributes and properties

        >>> class Foo(Record):
        ...     full = property(lambda a: a.fname + ' ' + a.lname)
        ...
        >>> f = Foo(fname='Joe', lname='Smith')
        >>> f.full
        'Joe Smith'
        >>> f['full']
        'Joe Smith'
        >>> 'The name is %(full)s' % f
        'The name is Joe Smith'
        >>> print(f)
        Foo
          fname ...............: 'Joe'
          lname ...............: 'Smith'
          full ................: 'Joe Smith'

        >>> f.attributes()
        ['fname', 'lname', 'full']

        >>> class FooBar(Record):
        ...     full = property(lambda a: a.fname + ' ' + a.lname)
        ...
        >>> o = FooBar(a=2)
        >>> kind(o)
        'foo_bar'
        >>> o.a
        2
        >>> o['a']
        2
        >>> o.double = property(lambda o: 2*o.a)
        >>> o.double
        4
        >>> o['double']
        4
        >>> del o.a
        >>> print(o.a)
        None

        >>> class Foo(Record):
        ...     full = property(lambda a: a.fname + ' ' + a.lname)
        ...
        >>> f = Foo(fname='Joe', lname='Smith')
        >>> f.full
        'Joe Smith'
        >>> f['full']
        'Joe Smith'
        >>> 'The name is %(full)s' % f
        'The name is Joe Smith'
        >>> getattr(f,'full')
        'Joe Smith'

        >>> print(Foo(_id=1, fname='Jane', lname='Smith'))
        Foo
          fname ...............: 'Jane'
          lname ...............: 'Smith'
          full ................: 'Jane Smith'

        >>> o = Record(a=2)
        >>> o.a
        2
        >>> o['a']
        2
        >>> o.double = property(lambda o: 2*o.a)
        >>> o.double
        4
        >>> o['double']
        4
        >>> del o.a
        >>> o.a

    """

    def save(self):
        """save record"""
        logger = logging.getLogger(__name__)
        id = self['__store'].put(self)
        key = self['__store'].id_name
        logger.debug('saved record %s(%s=%r) to %r',
            self.__class__.__name__,
            key,
            self[key],
            self['__store']
        )
        return id

    def attributes(self):
        return get_attributes(self)

    def valid(self):
        return 1

    def allows(self, user, action):
        return True

    def get(self, name, *default):
        try:
            return self.__getitem__(name)
        except KeyError as k:
            if default:
                return default[0]
            raise k

    def __getitem__(self, name):
        try:
            value = dict.__getitem__(self, name)
            if hasattr(value, '__get__'):
                return value.__get__(self)
            else:
                return value
        except KeyError as k:
            try:
                return self.__class__.__dict__[name].__get__(self)
            except KeyError as k:
                raise k

    def __str__(self):
        return self.__repr__(pretty=True)

    def __repr__(self, pretty=False):

        name = self.__class__.__name__
        attributes = self.attributes()
        t = []

        items = [
            (key, self.get(key, None)) for key in attributes
            if not key.startswith('_')
        ]

        if pretty:
            for key, value in items:
                if callable(value):
                    v = value()
                else:
                    v = value
                t.append('  {} {}: {!r}'.format(
                    key,
                    '.'*(20-len(key[:20])),
                    v
                ))
            return '\n'.join([name] + t)

        else:
            for key, value in items:
                if callable(value):
                    v = value()
                else:
                    v = value
                t.append((repr(key), repr(v)))
            return '<%s {%s}>' % (
                name, ', '.join('%s: %s' % (k, v) for k, v in t)
            )


class DefaultRecord(Record):
    """
    A Record with default values

        >>> class Foo(DefaultRecord): pass
        >>> foo = Foo(name='Sam')
        >>> foo.name
        'Sam'
        >>> foo.phone
        ''
    """

    def __getitem__(self, name):
        try:
            return Record.__getitem__(self, name)
        except KeyError:
            return ''


class RecordList(list):
    """a list of Records"""

    def __str__(self):
        """
        represent as a string

            >>> import datetime
            >>> class Person(Record): pass
            >>> class People(RecordList): pass
            >>> people = People()
            >>> people.append(Person(_id=1, name='Joe', age=20,
            ...     birthdate=datetime.date(1992,5,5)))
            >>> people.append(Person(_id=2, name='Samuel', age=25,
            ...     birthdate=datetime.date(1992,4,5)))
            >>> people.append(Person(_id=3, name='Sam', age=35,
            ...     birthdate=datetime.date(1992,3,5)))
            >>> print(people)
            person
            _id name   age birthdate
            --- ------ --- ----------
              1 Joe     20 1992-05-05
              2 Samuel  25 1992-04-05
              3 Sam     35 1992-03-05
            3 person records

            >>> people = People()
            >>> people.append(Person(userid=1, name='Joe', age=20,
            ...     birthdate=datetime.date(1992,5,5)))
            >>> people.append(Person(userid=2, name='Samuel', age=25,
            ...     birthdate=datetime.date(1992,4,5)))
            >>> people.append(Person(userid=3, name='Sam', age=35,
            ...     birthdate=datetime.date(1992,3,5)))
            >>> print(people)
            person
            userid name   age birthdate
            ------ ------ --- ----------
                 1 Joe     20 1992-05-05
                 2 Samuel  25 1992-04-05
                 3 Sam     35 1992-03-05
            3 person records

        """

        def visible(name):
            return not name.startswith('__')

        if not bool(self):
            return 'Empty list'

        title = '%s\n' % kind(self[0])

        keys = labels = list(filter(visible, get_attributes(self[0])))
        rows = [[record.get(key, None) for key in keys] for record in self]

        footer = '\n{} {} records'.format(len(self), kind(self[0]))

        return title + str(ItemList(rows, labels=labels)) + footer

    def __init__(self, *a, **k):
        list.__init__(self, *a, **k)
        self._n = 0

    def __iter__(self):
        self._n = 0
        return self

    def __next__(self):
        if self._n >= len(self):
            raise StopIteration
        else:
            result = self[self._n]
            self._n += 1
        return result


def matches(item, terms):
    """Returns True if an item matches search terms"""
    if not terms: return True
    v = [str(i).lower() for i in item.values()]
    return all(any(t in s for s in v) for t in terms)


def search(items, text):
    """Returns items that match search terms"""
    search_terms = list(set([i.lower() for i in text.strip().split()]))
    for item in items:
        if matches(item, search_terms):
            yield item
