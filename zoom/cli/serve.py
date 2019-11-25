"""server: Serve an instance for development.

Usage: zoom serve [options] [<instance>]

Options:
  -h, --help                  Show this message and exit.
  -v, --verbose               Run in verbose mode.
  -p, --port=<val>            The port to serve from.
  -n, --noop                  Use special debugging middleware stack.
  -u, --user=<val>            The user to run as.
  -f, --filter=<val>          The log filter.
  -r, --reloader              Whether to use the reloader.

Parameters:
  instance                    The Zoom instance directory. Defaults to the
                              instance directory at or above CWD."""

import logging
import os
import sys

from werkzeug.serving import run_simple
from docopt import docopt

from zoom import middleware
from zoom.server import WSGIApplication
from zoom.cli.utils import resolve_path_with_context, is_instance_dir, finish

def setup_logging(filter_, verbose):
    """Configure logging for this service runtime using the given filter and
    verbose flag value."""
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

def serve(_arguments=None):
    arguments = _arguments or docopt(__doc__)

    # Resolve the instance directory.
    instance = resolve_path_with_context(
        arguments['<instance>'] or '.',
        instance=True
    )
    # Assert it exists.
    if not is_instance_dir(instance):
        finish(True, '"%s" is not a valid directory'%instance)

    # Set up logging.
    setup_logging(arguments['--filter'], arguments['--verbose'])

    # Comprehend options.
    handlers = None
    if arguments['--noop']:
        handlers = middleware.DEBUGGING_HANDLERS
    user = arguments['--user']
    reloader = arguments['--reloader']
    port = arguments['--port'] or 80
    try:
        port = int(port)
    except ValueError:
        finish(True, 'Invalid port %s'%port)

    # Create the application.
    print('Serving Zoom instance at "%s"'%instance)
    app = WSGIApplication(instance=instance, handlers=handlers, username=user)
    try:
        # Run.
        run_simple('localhost', port, app, use_reloader=reloader)
    except (PermissionError, OSError) as err:
        finish(True, (
            '%s: is port %s in use?\n'
            'Use -p or --port to specify another port'
        )%(err.__class__.__name__, port))
serve.__doc__ = __doc__

# Legacy alias.
def server():
    serve(docopt(server.__doc__))
server.__doc__ = serve.__doc__.replace('zoom serve', 'zoom server')
