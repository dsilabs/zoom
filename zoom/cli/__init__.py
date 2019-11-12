# -*- coding: utf-8 -*-
"""Usage: zoom [options] [<command>] [<command-arg>...]

Commands:
  new           Create a new app, theme, or instance.
  server        Serve a Zoom instance for development.

Legacy commands (deprecated):
  database      Manage a database.
  setup         Set up a new Zoom instance.

Options:
  -h, --help    Show this message and exit. If used in conjunction with a
                command, show the usage for that command instead.
  -v, --verbose Run in verbose mode.
  -V, --version Show the Zoom version and exit."""

import os
import sys
import inspect

from docopt import docopt

from zoom.__version__ import __version__
from zoom.utils import ItemList

def finish(failure=False, *messages):
    for message in messages:
        print(message, file=sys.stderr)
    sys.exit(1)

# Legacy commands.
from zoom.cli.setup import setup
from zoom.cli.database import database
# Modern commands.
from zoom.cli.new import new
from zoom.cli.server import server

COMMANDS = {
    'new': new,
    'setup': setup,
    'database': database,
    'server': server
}

def run_cli():
    """The CLI entry point callable."""
    version_string = ' '.join(('zoom', __version__))
    arguments = docopt(
        __doc__, version=version_string, options_first=True,
        help=False
    )

    show_help = arguments['--help']
    command = arguments['<command>']
    if command:
        if command not in COMMANDS:
            finish(True, 'Invalid command: %s.\n'%command, __doc__)

        handler = COMMANDS[command]
        if show_help:
            finish(True, handler.__doc__)

        handler()
    else:
        if show_help:
            finish(False, __doc__)
        else:
            finish(True, 'No command specified (nothing to do).\n', __doc__)
