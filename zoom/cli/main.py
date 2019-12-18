"""Usage: zoom [options] [<command>] [<command-arg>...]

Commands:
  init                        Initialize a Zoom instance directory.
  new                         Create a new app, theme, database, or site.
  assign                      Link Zoom resources.
  describe                    Describe Zoom resources.
  serve                       Serve a Zoom instance.

Legacy commands (deprecated):
  database                    Manage a database.
  setup                       Set up a new Zoom instance.
  server                      Serve a Zoom instance for development.

Options:
  -h, --help                  Show this message and exit. If used in
                              conjunction with a command, show the usage for
                              that command instead.
  -V, --version               Show the Zoom version and exit."""

import os
import sys

from docopt import docopt

from zoom.__version__ import __version__
from zoom.utils import ItemList

from zoom.cli.utils import finish

from zoom.cli.setups import setup
from zoom.cli.database import database
from zoom.cli.new import new
from zoom.cli.serve import serve, server
from zoom.cli.init import init
from zoom.cli.assign import assign
from zoom.cli.describe import describe

COMMANDS = {
    'new': new,
    'setup': setup,
    'database': database,
    'server': server,
    'serve': serve,
    'init': init,
    'assign': assign,
    'describe': describe
}
DEPRECATED_COMMANDS = ('database', 'setup', 'server')

def main():
    """The CLI entry point callable. Handles dispatch to per-command handlers,
    as well as help provision."""
    version_string = ' '.join(('zoom', __version__))
    arguments = docopt(
        __doc__, version=version_string, options_first=True,
        help=False
    )

    show_help = arguments['--help']
    command = arguments['<command>']
    if command:
        if command not in COMMANDS:
            finish(True, 'Invalid command: %s\n'%command, __doc__)
        elif command in DEPRECATED_COMMANDS:
            print(
                'Warning: the %s command is deprecated'%command,
                file=sys.stderr
            )

        # Resolve the handler and either provide its help or invoke it.
        handler = COMMANDS[command]
        if show_help:
            finish(False, handler.__doc__)
        handler()
    else:
        if show_help:
            finish(False, __doc__)
        else:
            finish(True, 'No command specified (nothing to do)\n', __doc__)
