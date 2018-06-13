# -*- coding: utf-8 -*-

"""
    zoom CLI

    Zoom command line utility.
"""

# pylint: disable=unused-argument

import logging
import os
import shutil
import sys
from argparse import ArgumentParser


def make_app(pathname, template):
    template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'apps', template)
    if os.path.isdir(template_dir):
        shutil.copytree(template_dir, pathname)
    else:
        print('no template called {!r} {!r}'.format(template, template_dir))

def new(name=None):
    """create an app"""

    parser = ArgumentParser(
        description='create a new app',
        usage='zoom new [options] name'
    )

    parser.add_argument("-v", "--verbose", action='store_true',
                        help='verbose console logging')
    parser.add_argument('name', nargs='?', default=None)
    args = parser.parse_args()

    pathname = args.name
    if pathname:
        try:
            make_app(pathname, 'basic')
        except FileExistsError as e:
            print(pathname, 'exists')
            sys.exit(1)
    else:
        print('missing app name (-h for help)')
