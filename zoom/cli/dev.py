"""
ZoomFoundry Development Server

Usage: zoom dev [options] [<instance>]

Options:
  -h --help            Show this screen.
  -u, --user=<val>     The user to run as.
  -p, --port=<val>     The port to serve from [default: 8000].
  -v --verbose         Verbose logging.

Parameters:
  instance                    The Zoom instance directory. Defaults to the
                              instance directory at or above CWD.
"""

import logging
import os
import sys

import flask
from docopt import docopt
from livereload import Server

from zoom.tools import zoompath
from .reloader import get_blueprint


logger = logging.getLogger(__name__)


class CustomServer(Server):

    def _setup_logging(self):
        super()._setup_logging()

        # gets rid of Browser Connected messages
        logging.getLogger('livereload').setLevel(logging.WARNING)

        # set log level of built-in web server
        logging.getLogger('tornado.access').setLevel(logging.INFO)
        # logging.getLogger('tornado.application').setLevel(logging.INFO)


class ColoredConsoleHandler(logging.StreamHandler):
    """
        custom console log handler with coloured entries
    """

    def emit(self, record):
        levelno = record.levelno
        if levelno >= 50:  # CRITICAL / FATAL
            color = '\x1b[31m'  # red
        elif levelno >= 40:  # ERROR
            color = '\x1b[31m'  # red
        elif levelno >= 30:  # WARNING
            color = '\x1b[33m'  # yellow
        elif levelno >= 20:  # INFO
            color = '\x1b[32m'  # green
        elif levelno >= 10:  # DEBUG
            color = '\x1b[35m'  # pink
        else:  # NOTSET and anything else
            color = '\x1b[0m'  # normal
        record.color = color
        record.nocolor = '\x1b[0m'
        record.location = '%s:%s' % (record.module, record.lineno)
        logging.StreamHandler.emit(self, record)


class LiveReloadFilter(logging.Filter):
    """
        livereload log message filter
    """

    def filter(self, record):
        # print('livereload', record.module, record.getMessage())
        if 'livereload' in record.getMessage():
            return 0
        return 1


class AppFilter(logging.Filter):
    """
        autoreload and wsgi message filter
    """

    def filter(self, record):
        if record.module in ('wsgi', 'autoreload'):
            # suppress these messages because they are already handled by
            # the tornado console handler.
            return 0
        return 1


def setup_logging(level=logging.INFO):
    """Set up custom logging"""
    DEFAULT_FORMAT = (
        '%(color)s[%(levelname)1.1s %(asctime)s '
        '%(location)s]%(nocolor)s %(message)s'
    )
    DATE_FORMAT = '%y%m%d %H:%M:%S'

    con_formatter = logging.Formatter(DEFAULT_FORMAT, datefmt=DATE_FORMAT)
    console_handler = ColoredConsoleHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(con_formatter)
    console_handler.addFilter(AppFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)

    # filter livereload log entries
    tornado_logger = logging.getLogger('tornado.access')
    tornado_logger.addFilter(LiveReloadFilter())


def serve(app, port, level):
    server = CustomServer(app.wsgi_app)
    root = os.path.realpath('.')
    server.watch(root)
    setup_logging(level)
    logger.info('watching %s', root)
    server.serve(port=port)


def dev():
    arguments = docopt(__doc__, version='1.0.0')

    level = logging.INFO
    if arguments['--verbose']:
        level = logging.DEBUG

    port = int(arguments['--port'])
    username = arguments['--user']

    static_folder = zoompath('zoom/_assets/web/www/static')
    app = flask.Flask(__name__, static_folder=static_folder)
    app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension') # pylint: disable=no-member
    app.debug = True

    blueprint = get_blueprint(username=username)
    app.register_blueprint(blueprint)
    serve(app, port=port, level=level)


if __name__ == '__main__':
    dev()
