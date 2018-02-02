"""
    zoom.sql

    sql utilities
"""

import itertools

import zoom

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
