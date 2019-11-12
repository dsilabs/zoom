"""
    zoom server cli
"""

import logging
import os
import sys
from argparse import ArgumentParser

from zoom.cli.command import Command, CommandFailure

def setup_logging(filter_, verbose):
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

    if filter_:
        console_handler.addFilter(logging.Filter(name=filter_))
    
    if verbose:
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)

    for handler in root_logger.handlers:
        handler.setFormatter(con_formatter)

class ServerCommand(Command):
    arguments = (
        ('instance', 'The Zoom instance directory to serve; defaults to legacy directory.'),
    )
    options = (
        ('port', 'p', 'The port to serve from.'),
        ('noop', 'n', 'Use special debugging middleware stack.'),
        ('user', 'u', 'The user to use for runtime.'),
        ('filter', 'f', 'The log filter.')
    )

    def run(self):
        from zoom import middleware
        from zoom.server import run as runweb
        
        instance = self.get_argument('instance', take_input=False)
        if instance and not os.path.exists(instance):
            raise CommandFailure('%s is not a valid directory'%instance)

        setup_logging(self.get_option('filter', typ=str), self.verbose)

        handlers = None
        if self.get_option('noop'):
            handlers = middleware.DEBUGGING_HANDLERS
        user = self.get_option('user')

        port = self.get_option('port', default=80)
        try:
            port = int(port)
        except ValueError:
            raise CommandFailure('Invalid port %s')

        try:
            runweb(
                port=port, instance=instance, 
                handlers=handlers, username=user
            )
        except (PermissionError, OSError) as err:
            raise CommandFailure((
                '%s: is port %s in use?\n'
                'Use -p or --port to specify another port'
            )%(err.__class__.__name__, port))
