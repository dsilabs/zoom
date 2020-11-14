"""
    zoom.sql

    sql utilities
"""

import datetime
import decimal
import itertools

import zoom


class SearchTerm(object):

    def __init__(self, value):
        self.value = value

    def visit(self, visitor, *a, **k):
        return visitor(self, *a, **k)


class LessThan(SearchTerm):
    operator = '<'


class LessThanOrEqualTo(SearchTerm):
    operator = '<='


class GreaterThan(SearchTerm):
    operator = '>'


class GreaterThanOrEqualTo(SearchTerm):
    operator = '>='


class Equal(SearchTerm):
    operator = '=='


class NotEqual(SearchTerm):
    operator = '<>'


class Occurs(SearchTerm):
    operator = ' in '


class NotOccurs(SearchTerm):
    operator = ' not in '


# common aliases
lt = less_than = LessThan
le = lte = less_than_or_equal_to = LessThanOrEqualTo
gt = greater_than = GreaterThan
ge = gte = greater_than_or_equal_to = GreaterThanOrEqualTo
eq = equal = equals = Equal
ne = not_equal = not_equal_to = NotEqual
occurs = is_in = Occurs
not_occurs = is_not_in = NotOccurs


def make_table_select(table, *args, **kwargs):
    """Return select a statement and parameter list
    corresponding to the parameters provided.

    >>> make_table_select('people', name='Joe', age=less_than(3))
    ('select * from people where age<%s and name==%s', [3, 'Joe'])

    >>> make_table_select('people', name='Joe', age=less_than(4))
    ('select * from people where age<%s and name==%s', [4, 'Joe'])

    >>> make_table_select('people', name='Joe', age=occurs([4]))
    ('select * from people where age in %s and name==%s', [[4], 'Joe'])

    """

    def visitor(term):
        return term.operator, term.value

    def express(k, v):
        if isinstance(v, SearchTerm):
            return (k, v.visit(visitor))
        else:
            return (k, ('==', v))

    pairs = sorted(list(express(k, v) for k, v in kwargs.items()))
    expr, values = (
        ' and '.join('%s%s%s' % (v[0], v[1][0], '%s') for v in pairs),
        [v[1][1] for v in pairs],
    )
    cmd = 'select %s from %s where %s'
    return cmd % (args and ','.join(args) or '*', table, expr), values


def entify(attributes):
    """Convert a store result to a list of dicts
    """
    dictrec = zoom.utils.Bunch(klass=dict)
    result = zoom.store.entify(
        (
            (None, None, row_id, attribute, datatype, value)
            for row_id, attribute, datatype, value in attributes
        ),
        dictrec
    )
    for rec in result:
        del rec['__store']
    return zoom.utils.RecordList(result)


def make_store_select(kind, *a,**k):
    """Return an EntityStore query

    >>> sql = make_store_select('person', name='Joe', age=gt(25))
    >>> target = (
    ...     'select row_id, attribute, datatype, value from attributes where kind="person" and \\n'
    ...     '  row_id in (select row_id from attributes where kind="person" and attribute="age" and CAST(value AS INTEGER)>25) and\\n'
    ...     '  row_id in (select row_id from attributes where kind="person" and attribute="name" and value="Joe")'
    ... )
    >>> sql == target
    True

    >>> sql = make_store_select('person', birthdate=le(datetime.date(2020,1,1)))
    >>> target = (
    ...    'select row_id, attribute, datatype, value from attributes where kind="person" and \\n'
    ...    '  row_id in (select row_id from attributes where kind="person" and attribute="birthdate" and CAST(value AS DATE)<="2020-01-01")'
    ... )
    >>> sql == target
    True
    """

    def quote(text):
        return '"%s"' % text

    p = (
        '(select row_id from attributes '
        'where kind=%s and attribute=%s and %s)'
    )

    def visitor(term, name):

        def get_cast(value):
            get = {
                int: ('INTEGER', int),
                str: ('CHAR', str),
                datetime.datetime: ('DATETIME', quote),
                datetime.date: ('DATE', quote),
                float: ('DECIMAL', str),
                decimal.Decimal: ('DECIMAL', str)
            }.get
            return get(type(value))

        if isinstance(term.value, str):
            return p % (
                quote(kind),
                name,
                'value'+term.operator,
                term.value
            )
        else:
            cast_to, convert = get_cast(term.value)
            if cast_to is None:
                raise Exception('unknown type %r' % type(term.value))

            value = convert(term.value)

            return p % (
                quote(kind),
                quote(name),
                'CAST(value AS %s)%s%s' % (
                    cast_to,
                    term.operator,
                    value,
                ),
            )

    def express(k, v):
        if isinstance(v, SearchTerm):
            return v.visit(visitor, k)
        else:
            return p % (quote(kind), quote(k), 'value=' + quote(v))

    if a:
        start = 'select row_id, attribute, datatype, value from attributes where kind=' + quote(kind) + ' and attribute in ({}) '.format(
            ', '.join(quote(name) for name in sorted(a))
        ) + (' and' if k else '')
    else:
        start = 'select row_id, attribute, datatype, value from attributes where kind=' + quote(kind) + (' and ' if k else '')

    cmd = start + '\n' + ' and\n'.join('  row_id in %s' % express(k, v) for k,v in sorted(k.items()))

    return cmd


def setup_test():
    """setup test"""
    def create_test_tables(db):
        """create test tables"""
        db("""
        create table if not exists person (
            id integer PRIMARY KEY AUTOINCREMENT,
            name      varchar(100),
            age       integer,
            kids      integer,
            salary    decimal(10,2),
            birthdate date
            )
        """)

    def delete_test_tables(db):
        """drop test tables"""
        db('drop table if exists person')

    db = zoom.database.database('sqlite3', ':memory:')
    delete_test_tables(db)
    create_test_tables(db)
    return db


def summarize(table, dimensions, metrics=None):
    """
    summarize data

    >>> from zoom.records import Record, RecordStore
    >>> from decimal import Decimal
    >>> db = setup_test()
    >>> class Person(Record): pass
    >>> class People(RecordStore): pass
    >>> people = People(db, Person)
    >>> put = people.put
    >>> id = put(Person(name='Sam', age=25, kids=1, salary=Decimal('40000')))
    >>> id = put(Person(name='Sally', age=55, kids=4, salary=Decimal('80000')))
    >>> id = put(Person(name='Bob', age=25, kids=2, salary=Decimal('70000')))
    >>> id = put(Person(name='Jane', age=25, kids=2, salary=Decimal('50000')))
    >>> id = put(Person(name='Alex', age=25, kids=3, salary=Decimal('50000')))
    >>> print(people)
    person
    _id name  age kids salary
    --- ----- --- ---- ------
      1 Sam    25    1 40,000
      2 Sally  55    4 80,000
      3 Bob    25    2 70,000
      4 Jane   25    2 50,000
      5 Alex   25    3 50,000
    5 person records

    >>> print(summarize('person', ['age']))
    select "*" age, count(*) n from person group by 1
    union select age age, count(*) n from person group by 1


    >>> print(db(summarize('person', ['age'])))
    age n
    --- -
    25  4
    55  1
    *   5

    >>> print(db(summarize('person', ['age','kids'])))
    age kids n
    --- ---- -
    25  1    1
    25  2    2
    25  3    1
    25  *    4
    55  4    1
    55  *    1
    *   1    1
    *   2    2
    *   3    1
    *   4    1
    *   *    5

    >>> print(db(summarize('person', ['age','kids'], ['salary'])))
    age kids n salary
    --- ---- - -------
    25  1    1  40,000
    25  2    2 120,000
    25  3    1  50,000
    25  *    4 210,000
    55  4    1  80,000
    55  *    1  80,000
    *   1    1  40,000
    *   2    2 120,000
    *   3    1  50,000
    *   4    1  80,000
    *   *    5 290,000

    >>> people.zap()
    >>> print(people)
    Empty list
    """
    # pylint: disable=invalid-name
    # pylint: disable=unused-variable
    # pylint: disable=unused-argument
    # pylint: disable=possibly-unused-variable

    metrics = metrics or []

    statement_tpl = 'select {dims}, {calcs} from {table} group by {cols}'
    d = [i.split()[:1][0] for i in dimensions]
    c = [i.split()[-1:][0] for i in dimensions]
    n = len(dimensions)
    lst = []

    for s in list(itertools.product([0, 1], repeat=n)):
        dims = ', '.join(
            [s[i] and d[i] + ' '+ c[i] or '"*" ' + c[i]
             for i, _ in enumerate(s)]
        )
        calcs = ', '.join(
            ['count(*) n'] + ['sum({}) {}'.format(m, m)
                              for m in metrics]
        )
        cols = ', '.join([str(n+1) for n, _ in enumerate(c)])
        lst.append(statement_tpl.format(**locals()))

    return '\nunion '.join(lst)
