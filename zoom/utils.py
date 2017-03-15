# -*- coding: utf-8 -*-

"""
    zoom.utils
"""

import os
import collections


class ItemList(list):
    """
    list of data items

    >>> items = ItemList()
    >>> items.append(['Joe', 12, 125])
    >>> items
    [['Joe', 12, 125]]
    >>> print(items)
    Column 0  Column 1  Column 2  
    --------- --------- --------- 
    Joe       12        125      

    >>> items.insert(0, ['Name', 'Score', 'Points'])
    >>> print(items)
    Name  Score  Points  
    ----- ------ ------- 
    Joe   12     125    

    >>> data = [
    ...     ['Joe', 12, 125],
    ...     ['Sally', 13, 135],
    ... ]
    >>> items = ItemList(data)
    >>> print(items)
    Column 0  Column 1  Column 2  
    --------- --------- --------- 
    Joe       12        125      
    Sally     13        135      


    >>> data = [
    ...     ['Joe', 12, 125],
    ...     ['Sally', 13, 135],
    ... ]
    >>> items = ItemList(data, labels=['Name', 'Score', 'Points'])
    >>> print(items)
    Name   Score  Points  
    ------ ------ ------- 
    Joe    12     125    
    Sally  13     135    


    """
    def __init__(self, *args, **kwargs):
        self.labels = kwargs.pop('labels', None)
        list.__init__(self, *args, **kwargs)

    def __str__(self):
        def is_numeric(value):
            return type(value) in [int, float, Decimal]

        def is_text(value):
            return type(value) in [str, bytes]

        def name_column(number):
            return 'Column {}'.format(number)

        if len(self) == 0:
            return ''

        num_columns = len(self[0])

        # calculate labels
        if self.labels:
            labels = self.labels
            offset = 0
        else:
            # if first row is not all text it doesn't contain labels so generate them
            if not all(is_text(label) for label in self[0]):
                labels = [name_column(i) for i in range(num_columns)]
                offset = 0
            else:
                labels = self[0]
                offset = 1

        # calculate column lengths
        data_lengths = {}
        for rec in self[offset:]:
            for i, col in enumerate(rec):
                n = data_lengths.get(i, 0)
                m = len('%s' % rec[i])
                if n < m:
                    data_lengths[i] = m

        # sort columns by data length
        fields = list(data_lengths.keys())
        d = data_lengths
        fields.sort(key=lambda a: d[a])

        # make the various parts of the displayed list
        title = []
        lines = []
        fmtstr = []
        for i, label in enumerate(labels):
            width = max(len(label), d[i]) + 1
            fmt = '%-' + ('%ds'% width)
            fmtstr.append(fmt)
            title.append(fmt % label)
            lines.append(('-' * width) + '')
        title.append('\n')
        lines.append('\n')
        fmtstr = ' '.join(fmtstr)

        t = []

        for rec in self[offset:]:
            t.append(fmtstr % tuple(rec))

        return ' '.join(title) + ' '.join(lines) + '\n'.join(t)


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
