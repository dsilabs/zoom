"""assign: Link Zoom resources.

Usage:
    zoom assign database <database> [<site>]
    zoom assign theme <theme> [<site>]"""

import re
import os

from docopt import docopt

from zoom.config import Config
from zoom.cli.utils import resolve_path_with_context, is_site_dir,\
    which_argument, finish

def assign():
    # Parse the arguments and resolve what we're assigning.
    arguments = docopt(assign.__doc__)
    which = which_argument(arguments, ('database', 'theme'))

    # Resolve the site path into a site directory and assert we've done so.
    site_path = resolve_path_with_context(
        arguments['<site>'] or '.',
        site=True
    )
    if not is_site_dir(site_path):
        finish(True, 'Error: no Zoom site at "%s"'%site_path)

    # Load the site configuration.
    site_config = Config(site_path, 'site.ini')

    # Modify based on what assignment is being performed.
    if which == 'database':
        site_config.set('database', 'dbname', arguments['<database>'])
    elif which == 'theme':
        site_config.set('theme', 'name', arguments['<theme>'])
    else:
        raise NotImplementedError()

    # Save the result configuration.
    site_config.write()
    print('Updated "%s"'%site_config.config_pathname)
assign.__doc__ = __doc__
