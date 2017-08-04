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


def get_args():
    """Get command line arguments passed by user"""
    parser = argparse.ArgumentParser(
        description='manage the database',
        usage='zoom database [options] <command> ...'
        )

    parser.add_argument("-e", "--engine", type=str, default='sqlite3',
                        help='database engine (sqlite3 or mysql)')
    parser.add_argument("-H", "--host", type=str, default='localhost',
                        help='database host')
    parser.add_argument("-d", "--database", type=str, default='zoomdata',
                        help='database name')
    parser.add_argument("-P", "--port", type=int, default=3306,
                        help='database service port')
    parser.add_argument("-u", "--user", type=str, default='zoomuser',
                        help='database username')
    parser.add_argument("-p", "--password", type=str, default='zoompass',
                        help='database password')
    parser.add_argument("-v", "--verbose", action='store_true',
                        help='verbose console logging')
    parser.add_argument("-f", "--force", action='store_true',
                        help='force database creation (drop existing)')

    parser.add_argument('command', nargs=1, default=None, help='create, drop')
    parser.add_argument('args', nargs='*', default=None, help='database_name')
    return parser.parse_args()


def connect(engine, **kwargs):
    """Connect to the database specified"""
    if engine == 'mysql':
        mapping = {
            'host': 'host',
            'db': 'database',
            'port': 'port',
            'user': 'user',
            'passwd': 'password',
        }
    elif engine == 'sqlite3':
        mapping = {
            'database': 'database',
        }
        if not kwargs.get('database'):
            print('sqlite3 engine requires database name')
            sys.exit(-1)
    parameters = {key: kwargs.get(altkey) for key, altkey in mapping.items()}
    return zoom.database.database(engine, **parameters)


def get_parameters(args):
    """Extract database parameters from the arguments"""
    if args.engine == 'mysql':
        keys = 'engine', 'host', 'database', 'port', 'user', 'password'
    elif args.engine == 'sqlite3':
        keys = 'engine', 'database'
    parameters = {}
    for key in keys:
        if key in args:
            parameters[key] = getattr(args, key)
    return parameters


def list_databases(engine, parameters):
    """Print a list of databases"""
    if engine == 'mysql':
        engine_params = parameters.copy()
        if 'database' in engine_params:
            del engine_params['database']
        db = connect(**engine_params)
        print(db('show databases'))
    else:
        print('list command currently supports mysql engine only')


def show_tables(database, parameters):
    """Print a list of database tables"""
    db_params = parameters.copy()
    db_params['database'] = database
    db = connect(**db_params)
    print('\n'.join(db.get_tables()))


def create_database(args, name, parameters):
    """Create database tables"""
    if args.engine == 'mysql':
        # print(args, name, parameters)
        engine_params = parameters.copy()
        engine_params.pop('database')
        database_name = name
        db = zoom.database.database(**engine_params)
        if database_name in db.get_databases():
            if args.force:
                db('drop database %s', database_name)
            else:
                print('database {!r} exists'.format(database_name))
                sys.exit(-1)
        db('create database %s' % database_name)
        db('use %s' % database_name)

    elif args.engine == 'sqlite3':
        engine_params = parameters.copy()
        engine_params['name'] = os.path.join(
            'web',
            'sites',
        )
        db = connect(**parameters)

    else:
        print('create not yet supported for %r engine' % args.engine)
        sys.exit(-1)

    db.create_site_tables()
    logging.debug('finished creating site tables')


def update_site_config(site_name, parameters):
    """Update the site config to establish the database settings"""
    site_directory = os.path.join('web', 'sites', site_name)
    if not os.path.isdir(site_directory):
        print('site directory {} missing'.format(site_directory))
        sys.exit(-1)

    config_filename = os.path.join(site_directory, 'site.ini')

    if os.path.exists(config_filename):
        existing_config = configparser.ConfigParser()
        existing_config.read(config_filename)
        if existing_config.has_section('database'):
            print('database settings already exist in {}'.format(
                config_filename
            ))
            print(existing_config.options('database'))
            sys.exit(-1)

    new_config = configparser.RawConfigParser()
    new_config.add_section('database')
    for key, value in parameters.items():
        if key == 'database':
            key = 'name'
        new_config.set('database', key, value)

    with open(config_filename, 'a') as configfile:
        new_config.write(configfile)

    return new_config


def create_site_database(args, site_name):
    """Create site database"""
    site_directory = os.path.join('web', 'sites', site_name)

    config_filename = os.path.join(site_directory, 'site.ini')

    if os.path.exists(config_filename):
        config = configparser.ConfigParser()
        config.read(config_filename)
        if config.has_section('database'):
            engine = config.get('database', 'engine')
            if engine == 'sqlite3':
                pathname = os.path.join(
                    site_directory,
                    config.get('database', 'name') + '.sqlite3'
                )
                config.set('database', 'name', pathname)
                db = zoom.database.connect_database(config)

            elif engine == 'mysql':
                database_name = config.get('database', 'name')
                config.remove_option('database', 'name')
                db = zoom.database.connect_database(config)
                if database_name in db.get_databases():
                    if args.force:
                        db('drop database %s', database_name)
                    else:
                        print('database {!r} exists'.format(database_name))
                        sys.exit(-1)
                db('create database %s' % database_name)
                db('use %s' % database_name)

            db.create_site_tables()

        else:
            print('database settings missing in {}'.format(
                config_filename
            ))
            print(config.options('database'))
            sys.exit(-1)


def setup_site(args, site_name, parameters):
    """Setup a database for a site"""
    update_site_config(site_name, parameters)
    create_site_database(args, site_name)


def database():
    """manage the database"""

    args = get_args()
    if args.engine not in ['sqlite3', 'mysql']:
        print('{!r} is not a valid engine'.format(args.engine))
        sys.exit(-1)

    logger = logging.getLogger(__name__)
    if args.verbose:
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        logger.debug('verbose logging')

    parameters = get_parameters(args)
    command = args.command[0]

    if command == 'list':
        list_databases(args.engine, parameters)

    elif command == 'show':
        if args.args:
            show_tables(args.args[0], parameters)
        else:
            print('please provide database name')

    elif command == 'create':
        if args.args:
            create_database(args, args.args[0], parameters)
        else:
            print('please provide database name')

    elif command == 'setup':
        if args.args:
            setup_site(args, args.args[0], parameters)
        else:
            print('please provide site name')

    else:
        print('unknown command %r' % command)
        sys.exit(-1)

    #     elif command == 'setup':
    #
    #         engine = args.engine or 'mysql'
    #         if engine != 'mysql':
    #             msg = 'setup currently only works with mysql (not {!r})'
    #             print(msg.format(engine))
    #             sys.exit(-1)
    #
    #         if not args.args:
    #             site_name = 'localhost'
    #         else:
    #             site_name = args.args[0]
    #
    #         filename = os.path.join('web', 'sites', site_name, 'site.ini')
    #         if not os.path.isfile(filename):
    #             print('unable to find site directory: {}'.format(filename))
    #             sys.exit(-1)
    #
    #         config = zoom.utils.get_config(filename)
    #         get = config.get
    #         has_settings = any(
    #             get('database', key, None)
    #             for key in [
    #                 'engine', 'host', 'name', 'user', 'password', 'port',
    #             ]
    #         )
    #
    #         host = args.host or 'localhost'
    #         name = args.name or 'zoomdata'
    #         user = args.user or 'zoomuser'
    #         password = args.password or 'zoompass'
    #         port = args.port = 3306
    #
    #         print('\n'.join(repr(a) for a in locals().items()))
    #         sys.exit(0)
    #
    #         # if there are no current settings in the config file then
    #         # create them and store them in the config file
    #         if not has_settings:
    #             new_config = configparser.RawConfigParser()
    #             new_config.set('database', 'host', host)
    #             new_config.set('database', 'name', name)
    #             new_config.set('database', 'user', user)
    #             new_config.set('database', 'password', password)
    #             new_config.set('database', 'port', port)
    #
    #             with open(filename, 'a') as configfile:
    #                 if 'database' not in new_config.sections():
    #                     new_config.add_section('database')
    #                 keys = [
    #                     'engine', 'name', 'host', 'port', 'user', 'password'
    #                 ]
    #                 for key in keys:
    #                     new_config.set('database', key, locals()[key])
    #                 new_config.write(configfile)
    #
    #         # create the database
    #         config = zoom.utils.get_config(filename)
    #         config.config.set('database', 'user', args.user or 'root')
    #         config.config.set('database', 'password', args.password or 'root')
    #         if config.config.has_option('database', 'name'):
    #             config.config.remove_option('database', 'name')
    #         db = zoom.database.connect_database(config)
    #         if name in db.get_databases():
    #             if args.force:
    #                 db('drop database %s', name)
    #             else:
    #                 print('database {!r} exists'.format(name))
    #                 sys.exit(-1)
    #         db('create database %s', name)
    #         try:
    #             logger.debug(
    #                 'creating user %r identified by %r',
    #                 user,
    #                 password[:4] + '***'
    #             )
    #             db('create user %s identified by %s', user, password)
    #         except zoom.database.DatabaseException:
    #             logger.debug('unable to create user')
    #         db('grant all on %s.* to %s' % (name, user))
    #
    #         # connect as site user to create the tables
    #         config = zoom.utils.get_config(filename)
    #         db = zoom.database.connect_database(config)
    #         db.create_site_tables()
    #
    #     elif command == 'list':
    #         db = connect(engine, **parameters)
    #         print(db('show databases'))
    #
    #     else:
    #         logging.error('unknown command %r', command)
