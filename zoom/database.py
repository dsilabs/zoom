# -*- coding: utf-8 -*-

"""
    zoom.database

    a database that does less
"""

import timeit


class UnkownDatabaseException(Exception):
    pass


ARRAY_SIZE = 1000

ERROR_TPL = """
  statement: {!r}
  parameters: {}
  message: {}
"""


class Result(object):
    """database query result"""
    # pylint: disable=too-few-public-methods

    def __init__(self, cursor, array_size=ARRAY_SIZE):
        self.cursor = cursor
        self.array_size = array_size

    def __iter__(self):
        while True:
            results = self.cursor.fetchmany(self.array_size)
            if not results:
                break
            for result in results:
                yield result

    def __len__(self):
        # deprecate? - not supported by all databases
        count = self.cursor.rowcount
        return count > 0 and count or 0

    def __str__(self):
        """nice for humans"""
        labels = [' %s '%i[0] for i in self.cursor.description]
        values = [[' %s ' % i for i in r] for r in self]
        allnum = [
            all(str(v[i][1:-1]).translate({'.': None}).isdigit() for v in values)
            for i in range(len(labels))
        ]
        widths = [
            max(len(v[i]) for v in [labels] + values)
            for i in range(len(labels))
        ]
        fmt = ' ' + ' '.join([
            (allnum[i] and '%%%ds' or '%%-%ds') % w
            for i, w in enumerate(widths)
        ])
        lines = ['-' * (w) for w in widths]
        result = '\n'.join((fmt%tuple(i)).rstrip() for i in [labels] + [lines] + values)
        return result

    def __repr__(self):
        """useful and unabiguous"""
        return repr(list(self))

    def first(self):
        """return first item in result"""
        for i in self:
            return i


class Database(object):
    # pylint: disable=trailing-whitespace
    """
    database object

        >>> import sqlite3
        >>> db = database('sqlite3', database=':memory:')
        >>> db('drop table if exists person')
        >>> db(\"\"\"
        ...     create table if not exists person (
        ...     id integer primary key autoincrement,
        ...     name      varchar(100),
        ...     age       smallint,
        ...     kids      smallint,
        ...     birthdate date,
        ...     salary    decimal(8,2)
        ...     )
        ... \"\"\")

        >>> db("insert into person (name, age) values ('Joe',32)")
        1

        >>> db('select * from person')
        [(1, 'Joe', 32, None, None, None)]

        >>> print(db('select * from person'))
          id   name   age   kids   birthdate   salary
         ---- ------ ----- ------ ----------- --------
           1   Joe     32   None   None        None

    """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, factory, *args, **keywords):
        """Initialize with factory method to generate DB connection
        (e.g. odbc.odbc, cx_Oracle.connect) plus any positional and/or
        keyword arguments required when factory is called."""
        self.__connection = None
        self.__factory = factory
        self.__args = args
        self.__keywords = keywords
        self.debug = False
        self.log = []
        self.rowcount = None
        self.lastrowid = None

    def __getattr__(self, name):
        if self.__connection is None:
            self.__connection = self.__factory(*self.__args, **self.__keywords)
        return getattr(self.__connection, name)

    def _execute(self, cursor, method, command, *args):
        """execute the SQL command"""
        start = timeit.default_timer()
        params = len(args) == 1 and \
                hasattr(args[0], 'items') and \
                args[0] or \
                args
        try:
            method(command, params)
        except Exception as error:
            raise DatabaseException(ERROR_TPL.format(command, args, error))
        else:
            self.rowcount = cursor.rowcount
        finally:
            if self.debug:
                self.log.append('  SQL ({:5.1f} ms): {!r} - {!r}'.format(
                    (timeit.default_timer() - start) * 1000,
                    command,
                    args,
                ))

        if cursor.description:
            return Result(cursor)
        else:
            self.lastrowid = getattr(cursor, 'lastrowid', None)
            return self.lastrowid

    def execute(self, command, *args):
        """execute a SQL command with optional parameters"""
        cursor = self.cursor()
        return self._execute(cursor, cursor.execute, command, *args)

    def execute_many(self, command, sequence):
        """execute a SQL command with a sequence of parameters"""
        # pylint: disable=star-args
        cursor = self.cursor()
        return self._execute(cursor, cursor.executemany, command, *sequence)

    def __call__(self, command, *args):
        return self.execute(command, *args)

    def use(self, name):
        """use another database on the same instance"""
        # pylint: disable=star-args
        args = list(self.__args)
        keywords = dict(self.__keywords, db=name)
        return Database(self.__factory, *args, **keywords)

    def report(self):
        """produce a SQL log report"""
        if self.log:
            return '  Database Queries\n --------------------\n{}\n'.format(
                '\n'.join(self.log))
        return ''

def database(engine, *args, **kwargs):
    """create a database object"""
    # pylint: disable=invalid-name

    if engine == 'sqlite3':
        import sqlite3
        db = Database(sqlite3.connect, *args, **kwargs)
        return db

    else:
        raise UnkownDatabaseException
