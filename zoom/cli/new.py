# -*- coding: utf-8 -*-
"""
    zoom new cli
"""

# pylint: disable=unused-argument
import os
import shutil
import sys
from argparse import ArgumentParser

import zoom

from zoom.cli.command import Command, CommandFailure

class NewCommand(Command):
    arguments = (
        ('which', 'What to create; "site", "app", or "instance".'),
        ('path', 'The destination path for the created item.')
    )

    def run(self):
        which = self.get_argument('which')
        if which != 'app':
            raise CommandFailure('Invalid value for "which"')
        path = self.get_argument('path')

        try:
            make_app(path, 'basic')
        except FileExistsError:
            raise CommandFailure('%s at "%s" already exists'%(which, path))

        print('Created %s at "%s".'%(which, path))

def make_app(pathname, template):
    """Make an app from an app template"""
    template_dir = zoom.tools.zoompath('zoom', 'templates', 'apps', template)
    if os.path.isdir(template_dir):
        shutil.copytree(template_dir, pathname)
    else:
        print('no template called {!r} {!r}'.format(template, template_dir))
