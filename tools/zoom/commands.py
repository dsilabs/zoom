# -*- coding: utf-8 -*-

"""
    zoom CLI

    Zoom command line utility.
"""

# pylint: disable=unused-argument

import os
from argparse import ArgumentParser

__all__ = [
    'server',
]


def server(instance='.'):
    """run an instance using Python's builtin HTTP server"""

    parser = ArgumentParser(
        description='run a built-in zoom http server',
        usage='zoom server [options] instance'
        )

    parser.add_argument("-p", "--port", type=int, default=80,
                        help='service port')
    parser.add_argument("-n", "--noop", action='store_true',
                        help='use special debugging middleware stack')
    parser.add_argument('instance', nargs='?', default=os.getcwd())
    args = parser.parse_args()

    from zoom.server import run as runweb
    import zoom.middleware
    try:
        instance = os.path.abspath(args.instance or instance)
        if not os.path.exists(instance):
            print('Um, that\'s not a valid instance directory')
        else:
            if args.noop:
                handlers = zoom.middleware.DEBUGGING_HANDLERS
                runweb(port=args.port, instance=instance, handlers=handlers)
            else:
                runweb(port=args.port, instance=instance)
            print('\rstopped')
    except PermissionError:
        print('Permission Error: is port {} in use?\n'
              'use -p <port> to choose a different port'.format(args.port))
