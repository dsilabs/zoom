"""
    zoom database command
"""

import argparse
import configparser
import logging
import os
import sys
import warnings

import zoom
from zoom.database import (
    database as connect,
)

header_template = \
""";
; Zoom config for {}
;

"""


def database():
    """manage the database"""

    parser = argparse.ArgumentParser(
        description='manage the database',
        usage='zoom database [options] <command> ...'
        )

    parser.add_argument("-e", "--engine", type=str, default='sqlite3',
                        help='database engine (sqlite3 or mysql)')
    parser.add_argument("-H", "--host", type=str, default=None,
                        help='database host')
    parser.add_argument("-P", "--port", type=int, default=3306,
                        help='database service port')
    parser.add_argument("-u", "--user", type=str, default=None,
                        help='database username')
    parser.add_argument("-p", "--password", type=str, default=None,
                        help='database password')
    parser.add_argument("-v", "--verbose", action='store_true',
                        help='verbose console logging')
    parser.add_argument("-f", "--force", action='store_true',
                        help='force database creation (drop existing)')

    parser.add_argument('command', nargs=1, default=None, help='create, drop')
    parser.add_argument('args', nargs='*', default=None, help='database_name')
    args = parser.parse_args()

    # positionals = []
    parameters = {}
    logger = logging.getLogger(__name__)
    if args.verbose:
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        logger.debug('verbose logging')

    if args.engine not in ['sqlite3', 'mysql']:
        print('{!r} is not a valid engine'.format(args.engine))

    else:
        engine = args.engine

        if engine == 'sqlite3':
            if args.args:
                parameters['database'] = args.args[0]

        elif engine == 'mysql':
            if args.host:
                parameters['host'] = args.host
            if args.user:
                parameters['user'] = args.user
            if args.password:
                parameters['passwd'] = args.password
            # if args.args:
            #     parameters['db'] = args.args[0]

        # logger.error('connecting to %s %s', engine, parameters)

        command = args.command[0]
        if command == 'show':
            if not args.args:
                logging.error('database name missing')
            else:
                db = connect(engine, **parameters)
                print(db.get_tables())

        elif command == 'create':

            if not args.args:
                logging.error('database name missing')

            else:
                database_name = args.args[0]
                if engine == 'mysql':
                    logging.debug('creating site database %r' % database_name)
                    try:
                        db = connect(engine, **parameters)
                        print('creating database', database_name)
                        if args.force:
                            warnings.filterwarnings("ignore")
                            db('drop database if exists {}'.format(database_name))
                        db('create database {}'.format(database_name))
                    except Exception as e:
                        print('Error: ', e)
                    else:
                        db = connect(engine, database=database_name, **parameters)
                        db.create_site_tables()
                        logging.debug('finished creating site tables')
                        # print('done')

                elif engine == 'sqlite3':
                    logging.info('creating site database %r' % database_name)
                    db = connect(engine, **parameters)
                    db.create_site_tables()
                    logging.debug(db.get_tables())
                    logging.debug('finished creating site tables')

                else:
                    logging.error('create not implemented for %s engine' % engine)

        elif command == 'setup':

            engine = args.engine or 'mysql'
            if engine != 'mysql':
                print('setup currently only works with mysql (not {!r})'.format(engine))
                sys.exit(-1)

            if not args.args:
                site_name = 'localhost'
            else:
                site_name = args.args[0]

            database_name = 'zoom_' + site_name.replace('.', '_')
            database_user = 'zoomuser'

            filename = os.path.join('web', 'sites', site_name, 'site.ini')
            if not os.path.isfile(filename):
                print('unable to find site directory: {}'.format(filename))
                sys.exit(-1)

            # data_filename = os.path.join('web', 'sites', site_name, 'database.ini')

            config = zoom.utils.get_config(filename)
            get = config.get

            # get database settings if there are any
            engine = get('database', 'engine', 'mysql')
            host = get('database', 'host', '')
            name = get('database', 'name', '')
            user = get('database', 'user', '')
            password = get('database', 'password', '')
            port = get('database', 'port', '')

            # if we need them and there are none, attempt to create them
            if engine == 'mysql' and not (
                host or name or user or password or port
            ):

                host = 'localhost'
                name = database_name
                user = database_user
                password = 'zoompass'
                port = 3306

                new_config = configparser.RawConfigParser()
                # new_config.read(filename)

                with open(filename, 'a') as configfile:

                    # configfile.write(header_template.format(site_name))

                    if 'database' not in new_config.sections():
                        new_config.add_section('database')
                    keys = [
                        'engine', 'name', 'host', 'port', 'user', 'password'
                    ]
                    for key in keys:
                        new_config.set('database', key, locals()[key])

                    # old_keys = [
                    #     'dbname', 'dbhost', 'dbport',
                    #     'dbuser', 'dbpass'
                    # ]
                    # for key in old_keys:
                    #     if new_config.has_option('database', key):
                    #         new_config.remove_option('database', key)

                    new_config.write(configfile)

            # connect as root to create new database and user account
            config = zoom.utils.get_config(filename)
            config.config.set('database', 'user', args.user or 'root')
            config.config.set('database', 'password', args.password or 'root')
            if config.config.has_option('database', 'name'):
                config.config.remove_option('database', 'name')
            db = zoom.database.connect_database(config)
            if database_name in db.get_databases():
                if args.force:
                    db('drop database {}'.format(database_name))
                else:
                    print('database {!r} exists'.format(database_name))
                    sys.exit(-1)
            db('create database {}'.format(database_name))
            try:
                logger.debug(
                    'creating user %r identified by %r',
                    database_user,
                    password[:4] + '***'
                )
                db('create user %s identified by %s', database_user, password)
            except zoom.database.DatabaseException:
                logger.debug('unable to create user')
            db('grant all on %s.* to %s' % (database_name, database_user))

            # connect as site user to create the tables
            config = zoom.utils.get_config(filename)
            # if config.config.has_option('database', 'name'):
            #     config.config.remove_option('database', 'name')
            #     config.config.set('database', 'name', database_name)
            db = zoom.database.connect_database(config)
            db.create_site_tables()

        elif command == 'list':
            db = connect(engine, **parameters)
            print(db('show databases'))

        else:
            logging.error('unknown command %r', command)
