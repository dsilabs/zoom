"""
    zoom.browse
"""

from zoom.utils import name_for, sorted_column_names, Record
from zoom.components import as_actions
from zoom.html import tag, div


def browse(data, **kwargs):
    """browse data"""

    def getcol(item, index):
        if isinstance(item, dict):
            return item.get(index, None)
        elif isinstance(item, (tuple, list)):
            return item[index]
        else:
            return getattr(item, index)

    labels = kwargs.get('labels')
    fields = kwargs.get('fields')
    columns = kwargs.get('columns')
    title = kwargs.get('title')
    actions = kwargs.get('actions', [])
    header = kwargs.get('header')
    footer = kwargs.get('footer', '')

    items = list(data)

    if labels:
        if not columns:
            if len(items) and hasattr(items[0], 'get'):
                columns = [name_for(label).lower() for label in labels]

            elif len(items) and hasattr(items[0], '__len__') and len(items[0]):
                columns = range(len(labels))

            else:
                columns = [name_for(label).lower() for label in labels]

    else:
        if columns:
            labels = columns
        else:
            if (len(items) and isinstance(items[0], Record)):
                labels = columns = items[0].attributes()

            elif (len(items) and hasattr(items[0], 'keys') and
                    callable(getattr(items[0], 'keys'))):
                # list of dicts
                labels = columns = sorted_column_names(items[0].keys())

            elif len(items) and hasattr(items[0], '__dict__'):
                # list of objects
                labels = columns = [items[0].__dict__.keys()]

            elif hasattr(data, 'cursor'):
                # Result object
                labels = [c[0] for c in data.cursor.description]
                columns = range(len(labels))

            elif len(items) and hasattr(items[0], '__len__') and len(items[0]):
                # list of lists?
                labels = items[0]
                columns = range(len(items[0]))
                items = items[1:]

            else:
                if len(items):
                    raise Exception('%s' % hasattr(items[0],'__len__'))
                return '<div class="baselist"><table><tbody><tr><td>None</td></th></tbody></table></div>'

    columns = list(columns)
    labels = list(labels)

    if fields:
        lookup = fields.as_dict()
        for n, col in enumerate(columns):
            if col in lookup:
                better_label = lookup[col].label
            else:
                better_label = None
            if better_label:
                if n > len(labels):
                    labels.append(better_label)
                else:
                    labels[n] = better_label

        alist = []
        for item in items:
            fields.initialize(item)
            flookup = fields.display_value()
            row = [flookup.get(col, getcol(item, col)) for col in columns]
            alist.append(row)
    else:
        alist = [[getcol(item, col) for col in columns] for item in items]

    t = []
    if labels:
        t.append('<thead><tr>')

        colnum = 0
        for label in labels:
            colnum += 1
            t.append('<th>%s</th>' % label)

        t.append('</tr></thead>')

    t.append('<tbody>')

    count = 0
    for row in alist:
        count += 1
        t.append('<tr id="row-%s">' % (count))

        for item in row:
            try:
                value = str(item)
            except Exception:
                value = repr(item)
            wrapping = len(value) < 80 and ' nowrap' or ''
            cell_tpl = '<td {}>%s</td>'.format(wrapping)
            t.append(cell_tpl % value)

        t.append('</tr>')

    t.append('</tbody>')

    if not count:
        t.append('<tr><td colspan=%s>None</td></tr>' % len(labels))

    if not header:
        if title:
            header = '<div class="title">%s</div>' % title
        if actions:
            header += as_actions(actions)

    header_body = header and ('<div class="header">%s</div>' % header) or ''
    footer_body = footer and ('<div class="footer">%s</div>' % footer) or ''

    result = '\n'.join(
        ['<div class="baselist">'] +
        [header_body] +
        ['<table>'] + t + ['</table>'] +
        [footer_body] +
        ['</div>']
    )
    return result
