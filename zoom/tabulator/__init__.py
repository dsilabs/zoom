"""
    tabulator
"""

import datetime
from decimal import Decimal
import json
import uuid

import zoom
from zoom.components import as_actions
from zoom.utils import (
    name_for, sorted_column_names, Record,
)


class Column(Record):
    pass


class ColumnList(zoom.utils.RecordList):
    pass


class Tabulator(zoom.DynamicComponent):
    """Tabulator Widget"""

    def format(self, *args, **kwargs):
        zoom.requires('tabulator')
        return zoom.DynamicComponent.format(self, *args, **kwargs)


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
        elif label.endswith(' ID'):
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
    formats = []
    rows = items
    for col in range(len(columns)):
        values = [row[col] for row in rows]
        if is_homogeneous(values):
            formats.append(get_format(labels[col], values))
        else:
            formats.append(('{}', 'left'))
    return formats


def getcol(item, index):
    if isinstance(item, dict):
        return item.get(index, None)
    elif isinstance(item, (tuple, list)):
        return item[index]
    else:
        return getattr(item, index)


def tabulated(data, *args, **kwargs):
    """Returns Tabulated Data"""

    labels = kwargs.get('labels')
    fields = kwargs.get('fields')
    columns = kwargs.get('columns')
    # title = kwargs.get('title')
    # actions = kwargs.get('actions', [])
    # header = kwargs.get('header')
    # footer = kwargs.get('footer', '')
    selectable = kwargs.get('selectable')
    table_id = kwargs.get('table_id', 't'+uuid.uuid4().hex)
    before = kwargs.get('before', False)

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
            if items and hasattr(items[0], 'labels') and getattr(items[0], 'labels'):
                labels = columns = items[0].labels
                columns = [name_for(label).lower() for label in labels]

            elif items and isinstance(items[0], Record):
                labels = columns = sorted_column_names(set([
                    a for item in items
                    for a in item.attributes()
                    if not a.startswith('__')
                ]))

            elif (items and hasattr(items[0], 'keys') and
                  callable(getattr(items[0], 'keys'))):
                # list of dicts
                labels = columns = [
                    a for a in sorted_column_names(items[0].keys())
                    if not a.startswith('__')
                ]

            elif items and hasattr(items[0], '__dict__'):
                # list of objects
                labels = columns = [items[0].__dict__.keys()]

            elif hasattr(data, 'cursor'):
                # Result object
                labels = [c[0] for c in data.cursor.description]
                columns = range(len(labels))

            elif items and hasattr(items[0], '__len__') and items[0]:
                # list of lists?
                labels = items[0]
                columns = range(len(items[0]))
                items = items[1:]

            else:
                if items:
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

    def format_value(value, n):
        try:
            return formatters[n].format(value)
        except BaseException:
            return repr(value)

    rows = [
        dict({
            column: format_value(getattr(item, column), n)
            for n, column in enumerate(columns)
        }, id=item.id)
        for item in items
    ]

    tabulator = Tabulator()

    controller = zoom.utils.Bunch(url='/production')

    column_settings = ColumnList([
        Column(title=labels[i], name=columns[i], field=columns[i], sorter='string')
        for i in range(len(columns))
    ])

    item = items and items[0]

    before = before or (items and items[0] and getattr(items[0], 'before_tabulated'))
    if before:
        before(column_settings)

    column_options = []
    for setting in column_settings:
        column = dict(
            title=setting.title,
            field=setting.field,
        )
        if setting.sorter:
            column['sorter'] = setting.sorter
        if setting.formatter:
            column['formatter'] = setting.formatter
        if setting.width_grow:
            column['widthGrow'] = setting.width_grow
        if setting.align:
            column['hozAlign'] = setting.align
        if setting.editor:
            column['editor'] = setting.editor
        if setting.filter:
            column['headerFilter'] = setting.filter
        column_options.append(column)

    column_options = json.dumps(column_options, indent=2)

    has_row_actions = items and bool(item.actions)
    selectable = selectable or has_row_actions

    return tabulator.format(
        data=json.dumps(rows),
        table_id=table_id,
        controller=controller,
        column_options=column_options,
        has_row_actions=items and bool(item.actions) and 'true' or 'false',
        selectable=selectable and 'true' or 'false',
        actions=[]
    ).render()
