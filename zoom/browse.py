"""
    zoom.browse
"""

import datetime
from decimal import Decimal
import uuid

import zoom
from zoom.components import as_actions
from zoom.utils import (
    name_for, sorted_column_names, Record,
)


def is_homogeneous(values):
    """Return True if values have the same type"""
    if len(values) <= 1:
        return True
    for n, value in enumerate(values):
        if value is not None:
            rest = values[n:]
            col_type = type(value)
            for other in rest:
                if other and not isinstance(other, col_type):
                    return False
    return True


def get_format(label, values):
    """Return a suitable format string and alignment for columns"""
    alignment = 'left'
    first_non_null = list(
        map(type, [a for a in values if a is not None])
    )[:1]
    if first_non_null:
        data_type = first_non_null[0]
        if label in ['id', '_id', 'userid']:
            return '{}', 'right'
        elif data_type in [int, float, Decimal]:
            return '{:,}', 'right'
        elif data_type in [datetime.date]:
            return '{:%Y-%m-%d}', alignment
        elif data_type in [datetime.timedelta]:
            return '{:}', alignment
        elif data_type in [datetime.datetime]:
            return '{:%Y-%m-%d %H:%M:%S}', alignment
    return '{}', alignment


def calculate_styling(columns, labels, items):
    """Return calculated styling based on data content"""
    # print(columns)
    formats = []
    rows = items
    for col in range(len(columns)):
        values = [row[col] for row in rows]
        if is_homogeneous(values):
            formats.append(get_format(labels[col], values))
        else:
            formats.append(('{}', 'left'))
    return formats


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
    sortable = kwargs.get('sortable', False)
    table_id = kwargs.get('table_id', uuid.uuid4().hex)

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
            if len(items) and isinstance(items[0], Record):
                labels = columns = sorted_column_names(set([
                    a for item in items
                    for a in item.attributes()
                    if not a.startswith('__')
                ]))

            elif (len(items) and hasattr(items[0], 'keys') and
                  callable(getattr(items[0], 'keys'))):
                # list of dicts
                labels = columns = [
                    a for a in sorted_column_names(items[0].keys())
                    if not a.startswith('__')
                ]

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
    invisible = []
    formatters = []
    alignments = []

    if fields:
        invisible_labels = []
        lookup = fields.as_dict()

        for n, col in enumerate(columns):

            if col in lookup:
                field = lookup[col]
                better_label = field.label
                visible = field.visible and field.browse
                if visible:
                    alignments.append(field.alignment)
                    formatters.append(str)
            else:
                better_label = None
                visible = True
                values = [getcol(row, col) for row in items]
                formatter, alignment = get_format(col, values)
                alignments.append(alignment)
                formatters.append(formatter)

            if better_label:
                if n > len(labels):
                    labels.append(better_label)
                else:
                    labels[n] = better_label

            if not visible:
                invisible.append(col)
                invisible_labels.append(n)

        for n in reversed(invisible_labels):
            del labels[n]

        alist = []
        for item in items:
            fields.initialize(item)
            flookup = fields.display_value()
            row = [
                flookup.get(col, getcol(item, col))
                for col in columns
                if col not in invisible
            ]
            alist.append(row)
    else:
        alist = [[getcol(item, col) for col in columns] for item in items]
        styling = calculate_styling(columns, labels, alist)
        formatters = [s[0] for s in styling]
        alignments = [s[1] for s in styling]

    column_alignments = """
        .baselist tbody>tr>td:nth-child(%s) {
            text-align: right;
            padding-right: 20px;
        }
        .baselist thead>tr>th:nth-child(%s) {
            text-align: right;
            padding-right: 20px;
        }
    """

    alignment_css = ''.join(
        column_alignments % (n+1, n+1)
        for n, alignment in enumerate(alignments)
        if alignment == 'right'
    )

    css = alignment_css

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

        for n, item in enumerate(row):
            try:
                value = formatters[n].format(item)
            except BaseException:
                value = repr(item)
            wrapping = len(value) < 80 and ' nowrap' or ''
            cell_tpl = '<td{}>%s</td>'.format(wrapping)
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

    if sortable:
        zoom.requires('datatables')
        js = """
            $('#{}').DataTable( {{
            "lengthMenu": [[25, 50, 100, -1], [25, 50, 100, "All"]],
            "dom": '<if>rt<lp><"clear">',
            paging: false,
            "oLanguage": {{
            "sSearch": "Filter"
            }}
        }} );
        """.format(table_id)
        css += """
        .dataTables_filter label {
            font-weight: normal;
        }
        """
        zoom.Component(css=css, js=js).render()
        table_tag = '<table id="{}" >'.format(table_id)
    else:
        zoom.Component(css=css).render()
        table_tag = '<table>'

    result = '\n'.join(
        ['<div class="baselist">'] +
        [header_body] +
        [table_tag] + t + ['</table>'] +
        [footer_body] +
        ['</div>']
    )

    return result
