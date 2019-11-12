# -*- coding: utf-8 -*-
"""new: Create a new app, site, or instance.

Usage:
  zoom [options] new app [<path>]
  zoom [options] new site [<path>]
  zoom [options] new instance [<path>]

Options:
  -h, --help    Show this message and exit.
  -v, --verbose Run in verbose mode.
  -V, --version Show the Zoom version and exit.

Parameters:
  path          The directory path in which to create the app, site, or
                instance."""

# pylint: disable=unused-argument
import os
import shutil
import sys

from docopt import docopt

import zoom

from zoom.cli import finish

def make_app(pathname, template):
    """Make an app from an app template"""
    template_dir = zoom.tools.zoompath('zoom', 'templates', 'apps', template)
    if os.path.isdir(template_dir):
        shutil.copytree(template_dir, pathname)
    else:
        print('no template called {!r} {!r}'.format(template, template_dir))

def new():    
    arguments = docopt(__doc__, options_first=True)

    path = arguments['<path>']
    if not path:
        path = input('path (The path to the directory to create): ')
    if os.path.isdir(path):
        finish(True, "%s already exists."%path)

    if arguments['app']:
        make_app(path, 'basic')
    else:
        raise NotImplementedError()

    print('Created %s.'%path)
new.__doc__ = __doc__
