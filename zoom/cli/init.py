"""init: Initialize a Zoom instance.

Usage: zoom init [options] [<path>]

Options:
  -E, --empty                 Don't create a default site.
  -U, --unstyled              Don't create a default theme.
  -R, --replace               Replace the existing instance directory if there
                              is one.

Default site options:
  -n, --name=<val>            The name of the default site to create; default
                              "default".
%s

Parameters:
  path                        The path at which to initialize a new Zoom
                              instance."""

import os
import shutil

from docopt import docopt

from zoom.cli.common import DB_CREATION_OPTIONS, SITE_CREATION_OPTIONS,\
    do_site_creation
from zoom.cli.utils import describe_options, copy_boilerplate,\
    is_instance_dir, finish

def init():
    # Parse and comprehend arguments.
    arguments = docopt(init.__doc__)
    path = arguments['<path>'] or '.'
    with_creation = not os.path.exists(path)

    # Run initialization with safety.
    try:
        replace_existing = arguments.get('--replace')
        create_site = not arguments.get('--empty')
        create_theme = not arguments.get('--unstyled')

        # Handle the case of the destination directory already existing.
        if not with_creation and is_instance_dir(path):
            if replace_existing:
                # Remove the existing directory.
                shutil.rmtree(path)
                with_creation = True
            else:
                finish(True, (
                    'Failed to initialize in "%s" (already an instance '
                    'directory, use --replace to replace)'
                )%path)
        if with_creation:
            os.makedirs(path, exist_ok=True)

        # Copy instance boilerplate to the new instance directory.
        copy_boilerplate('instances/basic', path)

        if create_site:
            name = arguments.get('--name') or 'default'
            
            # Initialize the directory.
            default_site_dir = os.path.join(path, 'sites/default')
            os.mkdir(default_site_dir)
            
            # Perform the creation.
            do_site_creation(default_site_dir, name, arguments)
        if create_theme:
            # Copy theme boilerplate.
            # XXX: (Minimal) duplication from "new theme".
            default_theme_dir = os.path.join(path, 'themes/default')
            os.mkdir(default_theme_dir)
            copy_boilerplate('themes/basic', default_theme_dir)

        # Output a result description.
        op_description = ' (created)' if with_creation else str()
        print('Initialized in "%s"%s'%(path, op_description))
    except BaseException as ex: 
        # If an error occurred and we created the directory, remove it.
        if with_creation:
            try:
                shutil.rmtree(path)
            except: pass
        
        if isinstance(ex, SystemExit):
            raise ex

        finish(True, 'Failed to initialize in "%s" (%s)'%(path, str(ex)))
init.__doc__ = __doc__%describe_options((
    *SITE_CREATION_OPTIONS, *DB_CREATION_OPTIONS
))
