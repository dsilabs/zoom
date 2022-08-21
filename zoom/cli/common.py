"""CLI logic shared between commands."""

import re
import os
import sys
import uuid
import logging

from pymysql.err import OperationalError, InternalError

from zoom.database import database
from zoom.cli.utils import collect_options, copy_boilerplate, finish

# These options and options tables are used to allow easy option and option set
# re-use, as well as make wizarding missing CLI options easier. They are
# leveraged by applicable work.

# Option for which database engine to use.
DB_ENGINE_OPTION = ('e', 'engine', 'the database engine; "mysql" or "sqlite3"', 'mysql')
# Options required for database connection.
DB_ACCESS_OPTIONS = (
    ('u', 'user', 'the database user to perform the operation as'),
    (
        'p', 'password', 
        'the database password for the user performing this operation'
    )
)
# Options for referencing a database.
DB_REFERENCE_OPTIONS = (
    DB_ENGINE_OPTION,
    (
        'H', 'host', 'the database host address; default "localhost"',
        'localhost'
    ),
    (
        'd', 'database', 'the database name for this site; default "zoomdata"',
        'zoomdata'
    ),
    ('P', 'port', 'the database port for this site', '3306')
)
# Options for creating a database.
DB_CREATION_OPTIONS = (
    *DB_REFERENCE_OPTIONS,
    *DB_ACCESS_OPTIONS,
    (
        'f', 'force', 'whether to drop the existing database if one exists',
        False
    )
)
# Options for creating a site.
SITE_CREATION_OPTIONS = (
    ('v', 'db-user', 'the database user for this site', 'zoomdata'),
    (
        'q', 'db-password', 
        'the password for the database user for this site', 
        uuid.uuid4().hex
    ),
    ('S', 'skip-db', 'skip database initialization', False)
)
# Options for logging configuration.
LOGGING_OPTIONS = (
    ('v', 'verbose', 'whether to use verbose logging', False),
    ('f', 'filter', 'the log filter to use')
)

def setup_logging(arguments):
    """Configure logging for this runtime using the given docopt-generated
    arguments including logging options."""
    filter_str = arguments.get('--filter')
    verbose = arguments.get('--verbose')

    fmt = (
        '%(asctime)s %(levelname)-8s %(name)-20s '
        '%(lineno)-4s %(message)s'
    )
    con_formatter = logging.Formatter(fmt)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(con_formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)

    if filter_str:
        console_handler.addFilter(logging.Filter(name=filter_str))
    
    if verbose:
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)

    for handler in root_logger.handlers:
        handler.setFormatter(con_formatter)

def do_database_creation(argument_source, collected=dict()):
    """Perform a database creation, including wizarding for required values not
    present in the provided argument source parsed by docopt. The caller can
    supply a set of already-collected applicable options to prevent entry
    duplication."""

    # Decide which arguments need to be collected based on what has already
    # been collected; then collect those and merge the two sets.
    to_collect = list(filter(
        lambda option: option[1] not in collected, 
        DB_CREATION_OPTIONS
    ))
    collected = {
        **collected,
        **collect_options(argument_source, to_collect)
    }

    # Parse and pop some options from the collected set.
    engine = collected['engine']
    db_name = re.sub(r'[^\w_]', '_', collected.pop('database'))
    force = collected.pop('force')
    # Validate and cast port number.
    if 'port' in collected:
        try:
            collected['port'] = int(collected['port'])
        except ValueError:
            finish(True, 'Error: invalid port number')
    
    # Acquire a connection and maybe create a database based on the engine.
    db = None
    if engine == 'mysql':
        try:
            db = database(**collected)
        except (OperationalError, InternalError) as err:
            if not collected['password']:
                # The user may be attempting to initialize as a root user with
                # no configured password. pymysql doesn't let us authenticate
                # in that case, so we provide a (hopefully) helpful error.
                finish(True, 
                    'Error: invalid database credentials (authentication with'
                    ' empty passwords isn\'t supported)'
                )
            else:
                # Otherwise we provide a more generic error.
                finish(True, 'Error: invalid database credentials (%s)'%(
                    str(err)
                ))
        # If this database already exists drop it if this operation is forced
        # or die.
        if db_name in db.get_databases():
            if force:
                db('drop database %s'%db_name)
            else:
                finish(True, 'Error: database "%s" already exists'%db_name)
        # Create the database and switch to it.
        db('create database %s;'%db_name)
        db('use %s;'%db_name)
    elif engine == 'sqlite3':
        # TODO(sqlite3 support): We should not collect these options instead.
        # XXX(sqlite3 support): How do we handle --force for sqlite?
        if collected:
            finish(True, 'Error: sqllite3 doesn\'t support extra options')
        db = database('sqlite3', db_name)
    else:
        finish(True, 'Error: engine "%s" isn\'t supported yet'%engine)

    # Create the stock Zoom tables and return the active handle with some
    # collected metadata.
    db.create_site_tables()
    print('Created Zoom database "%s"'%db_name)
    return db, db_name, collected.pop('host')

def do_site_creation(dest_path, name, argument_source):
    """Perform a site creation, including wizarding for required values not
    present in the provided argument source parsed by docopt. Will initialize a
    database for the created site unless that behaviour is explicitly disabled
    by the CLI input. Note the caller must ensure the destination site
    directory exists and is valid."""

    # Populate the new site with boilerplate.
    copy_boilerplate('sites/basic', dest_path)

    print('Creating site...')
    # Load the boilerplate configuration...
    ini_path = os.path.join(dest_path, 'site.ini')
    with open(ini_path, 'r') as ini_file:
        ini = ini_file.read()
    # ...parse options from CLI input or collect with wizard...
    collected = collect_options(argument_source, (
        *SITE_CREATION_OPTIONS, *DB_REFERENCE_OPTIONS
    ))
    collected['name'] = name
    # ...insert into site configuration...
    for key in collected:
        if key in ('force', 'port', 'skip-db'): continue
        ini = ini.replace('{{%s}}'%key, collected[key])
    # ...and save.
    with open(ini_path, 'w') as ini_file:
        ini_file.write(ini)

    # Respect database initialization skip.
    if collected['skip-db']:
        return

    print('Initialize database...')
    # Create the database. Note we supply the values we've parsed/collected
    # in the previous step (engine, host, port, etc.).
    db, db_name, db_host = do_database_creation(argument_source)
    print('Creating user...')
    # Set up the user now described in the site configuration.
    db_user = collected['db-user']
    db_password = collected['db-password']
    existing = db(
        'select User, Host from mysql.user where User = "%s";'%db_user
    )
    if not len(existing):
        db('create user %s@%s identified by %s;', *(
            db_user, '%', db_password
        ))
        db('grant all on %s.* to %%s@%%s;'%db_name, *(
            db_user, '%'
        ))
        print('Done')
    else:
        db('grant all on %s.* to %%s@%%s;'%db_name, *(
            db_user, '%'
        ))
        print(
            'User already exists, granted (the password hasn\'t been changed!)'
        )
    