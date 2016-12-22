# -*- coding: utf-8 -*-

"""
    zoom.utils
"""

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
