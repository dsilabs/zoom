# -*- coding: utf-8 -*-

"""
    zoom.database

    A database module that does less.
"""

import collections
import inspect
import logging
import os
import timeit
import warnings
from decimal import Decimal

import zoom

__all__ = [
    'Database',
    'MySQLDatabase',
    'MySQLDatabaseTransaction',
    'Sqlite3Database',
    'Sqlite3DatabaseTransaction',
    'UnknownDatabaseException',
    'DatabaseException',
    'EmptyDatabaseException',
    'Result',
    'database',
    'connect_database',
]

warnings.filterwarnings("ignore", "Unknown table.*")

ARRAY_SIZE = 1000

ERROR_TPL = """
  statement: {!r}
  parameters: {}
  message: {}
"""

def obfuscate(text):
    """obfuscate text so it is recognizable without divulging it

    >>> obfuscate('12345')
    '1***5'

    >>> obfuscate('')
    ''

    """
    return text[:1] + '*' * (len(text) - 2) + text[-1:]

class UnknownDatabaseException(Exception):
    """exception raised when the database is unknown"""
    pass


class DatabaseException(Exception):
    """exception raised when a database server error occurs"""
    pass


class EmptyDatabaseException(Exception):
    """exception raised when a database is empty"""
    pass


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
        labels = list(map(lambda a: '{0}'.format(*a), self.cursor.description))
        return str(zoom.utils.ItemList(self, labels=labels))

    def __repr__(self):
        """useful and unambiguous"""
        return repr(list(self))

    def first(self):
        """return first item in result"""
        for i in self:
            return i


class Database(object):
    # pylint: disable=trailing-whitespace
    # pylint: disable=too-many-instance-attributes
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
    id name age kids birthdate salary
    -- ---- --- ---- --------- ------
     1 Joe   32 None None      None

    >>> create_person_table = \"\"\"
    ...     create table if not exists person (
    ...     id integer primary key autoincrement,
    ...     name      varchar(100),
    ...     age       smallint,
    ...     kids      smallint,
    ...     birthdate date,
    ...     salary    decimal(8,2)
    ...     )
    ... \"\"\"
    >>> insert_person = "insert into person (name, age) values (%s, %s)"
    >>> with database('sqlite3', database=':memory:') as db:
    ...    db(create_person_table)
    ...    db(insert_person, 'Joe', 32)
    ...    db('select * from person')
    1
    [(1, 'Joe', 32, None, None, None)]

    """

    paramstyle = 'pyformat'
    stats = []  # make this a class attribute to catch across instances
    debug = False  # make this a class attribute to catch across instances

    def __init__(self, factory, *args, **keywords):
        """Initialize with factory method to generate DB connection
        (e.g. odbc.odbc, cx_Oracle.connect) plus any positional and/or
        keyword arguments required when factory is called."""
        self.__connection = None
        self.__factory = factory
        self.__args = args
        self.__keywords = keywords
        self.log = []
        self.rowcount = None
        self.lastrowid = None

    def __getattr__(self, name):
        if self.__connection is None:
            self.__connection = self.__factory(*self.__args, **self.__keywords)
        return getattr(self.__connection, name)

    def translate(self, command, *args):
        """translate sql dialects

        The Python db API standard does not attempt to unify parameter passing
        styles for SQL arguments.  This translate routine attempts to do that
        for each database type.  For databases that use the preferred pyformat
        paramstyle nothing needs to be done.  Databases requiring other
        paramstyles should override this method to translate the command
        to the required style.
        """
        def issequenceform(obj):
            """test for a sequence type that is not a string"""
            if isinstance(obj, str):
                return False
            return isinstance(obj, collections.Sequence)

        if self.paramstyle == 'qmark':
            if len(args) == 1 and hasattr(args[0], 'items') and args[0]:
                # a dict-like thing
                placeholders = {key: ':%s' % key for key in args[0]}
                cmd = command % placeholders, args[0]
            elif len(args) >= 1 and issequenceform(args[0]):
                # a list of tuple-like things
                placeholders = ['?'] * len(args[0])
                cmd = command % tuple(placeholders), args
            else:
                # just one tuple-like thing
                placeholders = ['?'] * len(args)
                cmd = command % tuple(placeholders), args
            return cmd

        elif self.paramstyle == 'named':
            if len(args) == 1 and hasattr(args[0], 'items'):
                # a dict-like thing
                placeholders = {key: ':%s' % key for key in args[0]}
                cmd = command % placeholders, args[0]
            elif len(args) >= 1 and issequenceform(args[0]):
                # a list of tuple-like things
                placeholders = [':%d' % (n+1) for n in range(len(args[0]))]
                cmd = command % tuple(placeholders), args[0]
            else:
                # just one tuple-like thing
                placeholders = [':%d' % (n+1) for n in range(len(args))]
                cmd = command % tuple(placeholders), args
            return cmd

        else:
            params = len(args) == 1 and \
                hasattr(args[0], 'items') and \
                args[0] or \
                args
            return command, params

    def _execute(self, cursor, method, command, *args):
        """execute the SQL command"""

        def format_stack(stack):  # pragma:  no cover
            n = m = 0
            for n, item in enumerate(stack):
                if item[3] == 'run_app':
                    break
            for m, item in enumerate(stack):
                if not item[1].endswith('database.py'):
                    break
            return '<pre><small>{}</small></pre>'.format(
                '<br>'.join('{3} : line {2} in {1}'.format(
                    *rec
                ) for rec in stack[m:n])
            )

        start = timeit.default_timer()
        command, params = self.translate(command, *args)
        try:
            method(command, params)
        except Exception as error:
            raise DatabaseException(ERROR_TPL.format(command, args, error))
        else:
            self.rowcount = cursor.rowcount
        finally:
            if self.debug:
                elapsed = timeit.default_timer() - start
                self.log.append('  SQL ({:5.1f} ms): {!r} - {!r}'.format(
                    elapsed * 1000,
                    command,
                    args,
                ))
                source = format_stack(inspect.stack())
                type(self).stats.append(
                    (elapsed, repr(command), repr(args), source)
                )

        if cursor.description:
            return Result(cursor)
        else:
            self.lastrowid = getattr(cursor, 'lastrowid', None)
            return self.lastrowid or None

    def execute(self, command, *args):
        """execute a SQL command with optional parameters"""
        cursor = self.cursor()
        return self._execute(cursor, cursor.execute, command, *args)

    def execute_many(self, command, sequence):
        """execute a SQL command with a sequence of parameters"""
        cursor = self.cursor()
        return self._execute(cursor, cursor.executemany, command, *sequence)

    def __call__(self, command, *args):
        return self.execute(command, *args)

    def runs(self, sql, *args, **kwargs):
        """Run multiple SQL statements from a string

        The SQL statements in the soure string must be separated by a newline
        followed by a semicolon (i.e. '\n;').

        >>> sql = \"\"\"
        ... create temporary table last_seen as (
        ...     select user_id, max(timestamp) as timestamp
        ...     from log
        ...     where timestamp >= %(recent)s
        ...     group by 1
        ... );
        ...
        ... create temporary table recent_users as (
        ...     select
        ...         username, last_seen.timestamp
        ...     from users left join last_seen on users.id = last_seen.user_id
        ... );
        ... \"\"\"
        >>> db = zoom.sites.Site().db
        >>> four_weeks_ago = zoom.tools.today() - zoom.tools.one_week * 4
        >>> response = db.runs(sql, dict(recent=four_weeks_ago))
        >>> print(db('select username from recent_users order by username'))
        username
        --------
        admin
        guest
        user

        """

        def split(statements):
            """split the sql statements"""
            return list(filter(bool, map(str.strip, statements.split(';\n'))))

        logger = logging.getLogger(__name__)

        statements = split(sql)

        logger.debug('running %s SQL statements', len(statements))

        for statement in statements:
            self(statement, *args, **kwargs)

        logger.debug('ran %s SQL statements', len(statements))


    def run(self, filename, *args, **kwargs):
        """Run multiple SQL statements from a file

        The SQL statements in the soure file must be separated by a newline
        followed by a semicolon (i.e. '\n;').

        >>> db = zoom.sites.Site().db
        >>> four_weeks_ago = zoom.tools.today() - zoom.tools.one_week * 4
        >>> response = db.run('zoom/sql/get_recent_users.sql', dict(recent=four_weeks_ago))
        >>> print(db('select username from recent_users order by username'))
        username
        --------
        admin
        guest
        user

        """

        logger = logging.getLogger(__name__)
        if os.path.isfile(filename):

            logger.debug('running SQL statements from %s', filename)

            with open(filename) as f:
                return self.runs(f.read(), *args, **kwargs)

            logger.debug('ran SQL statements from %s', filename)

        else:
            msg = 'file %s missing' % filename
            logger.error(msg)
            raise DatabaseException(msg)

    def use(self, name):
        """use another database on the same instance"""
        args = list(self.__args)
        keywords = dict(self.__keywords, db=name)
        return type(self)(*args, **keywords)

    def report(self):   # pragma: no cover
        """produce a SQL log report"""
        if self.log:
            return '  Database Queries\n --------------------\n{}\n'.format(
                '\n'.join(self.log))
        return ''

    @classmethod
    def get_stats(cls):
        """Return the stats to the caller, clearing the list of what is returned

            We use a classmethod to support inheritance (over staticmethod)
        """
        result = list(cls.stats)  # get a copy of the list
        del cls.stats[:len(result)]  # clear the list, but more may have been added
        return result

    def get_tables(self):
        """get a list of database tables"""
        pass

    @property
    def database(self):
        """Returns an object containing database parameters"""
        return zoom.utils.Bunch(
            name=self.__keywords.get('db'),
            host=self.__keywords.get('host'),
            port=self.__keywords.get('port'),
            user=self.__keywords.get('user'),
        )

    def __enter__(self):
        return self

    def __exit__(self, *_):
        logger = logging.getLogger(__name__)
        logger.debug('closing %s connection',
            self.__class__.__name__)
        self.close()


class Sqlite3DatabaseTransaction(Database):

    def __init__(self, db):
        self.db = db

    def __enter__(self):
        self.save_isolation_level = self.db.isolation_level
        self.db.isolation_level = 'DEFERRED'
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is not None:
            self.db.rollback()
            result = False
        else:
            self.db.commit()
            result = True
        self.db.isolation_level = self.save_isolation_level
        return result


class Sqlite3Database(Database):
    """Sqlite3 Database"""

    paramstyle = 'qmark'

    def __init__(self, *args, **kwargs):
        """Initialize with standard sqlite3 parameters"""
        import sqlite3

        keyword_args = dict(
            kwargs,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )

        # add support for decimal types
        def adapt_decimal(value):
            """adapt decimal values to their string representation"""
            return str(value)

        def convert_decimal(bytetext):
            """convert bytesring representatinos of decimal values to actual
            Decimal values"""
            return Decimal(bytetext.decode())

        sqlite3.register_adapter(Decimal, adapt_decimal)
        sqlite3.register_converter('decimal', convert_decimal)

        Database.__init__(self, sqlite3.connect, *args, **keyword_args)

    def get_tables(self):
        """return table names"""
        cmd = 'select name from sqlite_master where type="table"'
        return [a[0] for a in self(cmd)]

    def create_site_tables(self, filename=None):
        """Create Sqlite3 version of site tables"""
        logger = logging.getLogger(__name__)
        filename = zoom.tools.zoompath('tools/zoom/sql/setup_sqlite3g.sql')
        self.run(filename)
        logger.debug('created tables from %s', filename)

    def create_test_tables(self):
        """create the extra test tables"""
        zoompath = zoom.tools.zoompath
        self.run(zoompath('zoom/sql/create_test_tables_sqlite3.sql'))
        self.create_site_tables()

    def delete_test_tables(self):
        """drop the extra test tables"""
        self('drop table if exists person')
        self('drop table if exists account')

    def transaction(self):
        return Sqlite3DatabaseTransaction(self)


class MySQLDatabaseTransaction(Database):

    def __init__(self, db):
        self.db = db

    def __enter__(self):
        self.save_autocommit = self.db.autocommit_mode
        self.db.autocommit(0)
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is not None:
            self.db.rollback()
            result = False
        else:
            self.db.commit()
            result = True
        self.db.autocommit(self.save_autocommit)
        return result


class MySQLDatabase(Database):
    """MySQL Database"""

    paramstyle = 'pyformat'

    def __init__(self, *args, **kwargs):
        """Initialize with standard pymysql parameters"""
        import pymysql

        keyword_args = dict(
            kwargs,
            charset='utf8'
        )

        Database.__init__(self, pymysql.connect, *args, **keyword_args)

    def get_tables(self):
        """return table names"""
        cmd = 'show tables'
        return [a[0] for a in self(cmd)]

    def get_databases(self):
        """return database names"""
        cmd = 'show databases'
        return [a[0] for a in self(cmd)]

    def create_site_tables(self):
        """create the tables for a site in a mysql server"""
        logger = logging.getLogger(__name__)
        filename = zoom.tools.zoompath('tools/zoom/sql/setup_mysql.sql')
        self.run(filename)
        logger.debug('created tables from %s', filename)

    def create_test_tables(self):
        """create the extra test tables"""
        self("""
            create table if not exists person (
                id int unsigned not null auto_increment,
                name      varchar(100),
                age       smallint,
                kids      smallint,
                birthdate date,
                PRIMARY KEY (id)
                )
        """)
        self("""
            create table if not exists account (
                account_id int unsigned not null auto_increment,
                name varchar(100),
                added date,
                PRIMARY KEY (account_id)
                )
        """)
        self.create_site_tables()

    def delete_test_tables(self):
        """drop the extra test tables"""
        self('drop table if exists person')
        self('drop table if exists account')

    def get_column_names(self, table):
        """return column names for a table"""
        rows = self('describe %s' % table)
        return tuple(rec[0].lower() for rec in rows)

    @property
    def connect_string(self):
        """Return a string representation of the connection parameters"""

        return 'mysql://{}{}@{}/{}'.format(
            self.user.decode('utf8'),
            self.password and ':' + obfuscate(str(self.password)) or '',
            str(self.host),
            self.db.decode('utf8'),
        )

    def __str__(self):
        return '<{} {!r}>'.format(
            self.__class__.__name__,
            self.connect_string,
        )

    def transaction(self):
        return MySQLDatabaseTransaction(self)

    def __del__(self):
        if self.open:
            logger = logging.getLogger(__name__)
            logger.debug('closing %s connection with del',
                self.__class__.__name__)
            self.close()


class MySQLdbDatabase(Database):   # pragma: no cover
    """MySQLdb Database

    deprecated - not avaialble for Python 3.6

    use MySQLDatabase instead
    """

    paramstyle = 'pyformat'

    def __init__(self, *args, **kwargs):
        import MySQLdb

        keyword_args = dict(
            kwargs,
            charset='utf8'
        )

        Database.__init__(self, MySQLdb.connect, *args, **keyword_args)


def database(engine, *args, **kwargs):
    """create a database object"""
    # pylint: disable=invalid-name

    if engine == 'sqlite3':
        kwargs.setdefault('isolation_level', None)  # autocommit
        db = Sqlite3Database(*args, **kwargs)
        return db

    elif engine == 'mysql':
        db = MySQLDatabase(*args, **kwargs)
        db.autocommit(1)
        return db

    elif engine == 'mysqldb':   # pragma: no cover
        db = MySQLdbDatabase(*args, **kwargs)
        db.autocommit(1)
        return db

    else:
        raise UnknownDatabaseException


def connect_database(config):
    """establish a database connection"""

    def get(name, default=None):
        """Get database parameters

        The standard way to name the parameters is without the db
        prefix however we still support the old names to allow a
        smooth transition from the old naming conventions.
        """
        if config.has_option('database', name):
            value = config.get('database', name)
        elif config.has_option('database', 'db' + name):
            value = config.get('database', 'db' + name)
        elif name == 'password' and config.has_option('database', 'dbpass'):
            value = config.get('database', 'dbpass')
        else:
            value = default
        return value

    engine = get('engine', 'sqlite3')

    if engine == 'mysql':
        host = get('host', 'localhost')
        name = get('name')
        user = get('user', 'testuser')
        password = get('password', 'password')
        parameters = dict(
            engine=engine,
            host=host,
            user=user,
        )
        if password:
            parameters['passwd'] = password
        if name:
            parameters['db'] = name

    elif engine == 'mysqldb':   # pragma: no cover
        host = get('host', 'localhost')
        name = get('name')
        user = get('user', 'testuser')
        password = get('password', 'password')
        parameters = dict(
            engine=engine,
            host=host,
            user=user,
        )
        if password:
            parameters['passwd'] = password
        if name:
            parameters['db'] = name

    elif engine == 'sqlite3':
        name = get('name', 'zoomdata')
        parameters = dict(
            engine=engine,
            database=name,
        )

    else:
        raise Exception('unknown database engine: {!r}'.format(engine))

    connection = database(**parameters)

    logger = logging.getLogger(__name__)
    if 'passwd' in parameters:
        parameters['passwd'] = '*hidden*'
    if 'password' in parameters:
        parameters['password'] = '*hidden*'

    if connection:
        logger.debug('database connected: %r', parameters)

    return connection


def handler(request, handler, *rest):
    """Connect a database to the site if specified"""
    site = request.site
    database_name = site.config.get(
        'database', 'name', site.config.get(
            'database', 'dbname', None  # legacy
        )
    )
    if database_name:
        site.db = connect_database(site.config)
        Database.debug = site.monitor_system_database

        if site.db.get_tables() == []:
            raise EmptyDatabaseException('Database is empty')

    else:
        logger = logging.getLogger(__name__)
        logger.error('no database specified for %s', site.name)
        raise zoom.exceptions.DatabaseMissingException('Database Missing')

    request.profiler.add('database initialized')
    result = handler(request, *rest)
    request.profiler.add('database finished')
    return result


def setup_test(engine=None):   # pragma: no cover
    """create a set of test tables"""

    get = os.environ.get
    engine = engine or get('ZOOM_TEST_DATABASE_ENGINE', 'mysql')

    if engine == 'mysql':
        db = database(
            'mysql',
            host=get('ZOOM_TEST_DATABASE_HOST', 'localhost'),
            user=get('ZOOM_TEST_DATABASE_USER', 'testuser'),
            passwd=get('ZOOM_TEST_DATABASE_PASSWORD', 'password'),
        )
        db('drop database if exists zoomtest')
        db('create database zoomtest')
        db('use zoomtest')
        db.create_test_tables()

    elif engine == 'memory':
        db = database(
            'sqlite3',
            database=':memory:'
        )
        db.delete_test_tables()
        db.create_test_tables()
    else:
        raise Exception('Invalid engine parameter: {!r}'.format(engine))
    return db
