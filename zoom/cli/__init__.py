# -*- coding: utf-8 -*-
"""Usage: zoom [-h | --help] [-v | --verbose] [-V | --version] [<command>] [<command-arg>...] [--<command-option>...]

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

from zoom.__version__ import __version__
from zoom.utils import ItemList
from zoom.cli.command import CommandFailure
# Legacy commands.
from zoom.cli.setup import setup
from zoom.cli.database import database
# Modern commands.
from zoom.cli.new import NewCommand
from zoom.cli.server import ServerCommand

COMMANDS = {
    'new': NewCommand,
    'server': ServerCommand
}
LEGACY_COMMANDS = {
    'setup': setup,
    'database': database
}

def parse_argv(argv):
    options = dict()
    arguments = list()

    def parse_option(item, prefix):
        if '=' in item:
            key, value, *rest = item.split('=')
            if rest:
                finish(True, 'Invalid argument "%s"'%item)
            options[prefix + key] = value
        else:
            options[prefix + item] = True

    for item in argv:
        if item.startswith('--'):
            parse_option(item[2:], '--')
        elif item.startswith('-'):
            parse_option(item[1:], '-')
        else:
            arguments.append(item)
    
    return arguments, options

def finish(failure=False, *messages):
    for message in messages:
        print(message, file=sys.stderr)
    sys.exit(1)

def run_cli():
    """The CLI entry point callable."""
    version_string = ' '.join(('zoom', __version__))
    arguments, options = parse_argv(sys.argv[1:])

    if options.get('-V') or options.get('--version'):
        print(version_string)

    verbose = options.get('--verbose') or options.get('-v')
    if verbose:
        print('%s CLI'%version_string)

    show_help = options.get('--help') or options.get('-h')

    command = arguments[0] if arguments else None
    if command:
        if command in LEGACY_COMMANDS:
            print((
                'WARNING: '
                'The %s command in deprecated; it may be removed in future' 
                ' releases\n'
            )%command, file=sys.stderr)
            LEGACY_COMMANDS[command](sys.argv[2:])
            return

        if command not in COMMANDS:
            finish(True, 'Invalid command: %s\n'%command, __doc__)

        handler = COMMANDS[command](arguments[1:], options, verbose)
        if show_help:
            finish(True, handler.describe_usage(command))

        try:
            handler.run()
        except CommandFailure as err:
            finish(True, str(err))
    else:
        if show_help:
            finish(False, __doc__)
        else:
            finish(True, 'No command specified (nothing to do)\n', __doc__)
