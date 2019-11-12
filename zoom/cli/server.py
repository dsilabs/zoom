"""server: Serve an instance for development.

Usage: zoom server [options] [<instance>]

Options:
  -h, --help              Show this message and exit.
  -v, --verbose           Run in verbose mode.
  -p, --port <port>       The port to serve from.
  -n, --noop              Use special debugging middleware stack.
  -u, --user <username>   The user to run as.
  -f, --filter <filter>   The log filter.

Parameters:
  instance      The Zoom instance directory."""

import logging
import os
import sys

from docopt import docopt

from zoom.cli import finish

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

def server():
    from zoom import middleware
    from zoom.server import run as runweb

    arguments = docopt(__doc__)

    instance = arguments['<instance>']
    if instance and not os.path.exists(instance):
        finish(True, '"%s" is not a valid directory.'%instance)

    setup_logging(arguments['--filter'], arguments['--verbose'])

    handlers = None
    if arguments['--noop']:
        handlers = middleware.DEBUGGING_HANDLERS
    user = arguments['--user']
    port = arguments['--port'] or 80
    try:
        port = int(port)
    except ValueError:
        finish(True, 'Invalid port %s'%port)

    try:
        runweb(
            port=port, instance=instance, 
            handlers=handlers, username=user
        )
    except (PermissionError, OSError) as err:
        raise finish(True, (
            '%s: is port %s in use?\n'
            'Use -p or --port to specify another port'
        )%(err.__class__.__name__, port))
server.__doc__ = __doc__
