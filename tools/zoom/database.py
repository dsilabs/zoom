"""
    zoom database command
"""

from argparse import ArgumentParser
import logging

from zoom.database import database as connect


def database():
    """run an instance using Python's builtin HTTP server"""

    parser = ArgumentParser(
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

    parser.add_argument('command', nargs=1, default=None)
    parser.add_argument('args', nargs='*', default=None)
    args = parser.parse_args()

    # positionals = []
    parameters = {}

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
            if args.args:
                parameters['db'] = args.args[0]

        logger = logging.getLogger(__name__)
        logger.error('connecting to %s %s', engine, parameters)

        command = args.command[0]
        if command == 'show':
            if not args.args:
                logging.error('database name missing')
            else:
                db = connect(engine, **parameters)
                print(db.get_tables())

        elif command == 'create':
            logging.error('create is not implemented')

        else:
            logging.error('unknown command %r', command)
