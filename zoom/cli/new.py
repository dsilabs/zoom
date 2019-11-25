# -*- coding: utf-8 -*-
"""new: Create a new app, theme, or site.

Usage:
  zoom new app [options] <name> [<path>]
  zoom new site [options] <name> [<path>]
  zoom new theme [options] <name> [<path>]
  zoom new database [options] <name>

Options:
  -v, --verbose               Run in verbose mode.

App specific options:
  --title=<val>               The title for the created app. Defaults to the
                              name.
  --icon=<val>                The icon name for the created app.

Site specific options:
%s

Database specific options:
%s

Parameters:
  path                        The directory path in which to create the app,
                              theme, or site."""

import os

from docopt import docopt

from zoom.cli.common import DB_CREATION_OPTIONS, SITE_CREATION_OPTIONS,\
    do_database_creation, do_site_creation
from zoom.cli.utils import describe_options, copy_boilerplate,\
    resolve_path_with_context, finish, which_argument

COMMAND_PATH_CONTEXTS = {
    'app': ('apps', {'instance': True, 'site': True}),
    'theme': ('themes', {'instance': True, 'site': True}),
    'site': ('sites', {'instance': True}),
}

def new_filesystem_resource(arguments, command, name):
    path = arguments['<path>'] or '.'

    context_options = COMMAND_PATH_CONTEXTS[command]
    path = os.path.join(resolve_path_with_context(
        path, context_options[0], **context_options[1]
    ), name)

    if os.path.exists(path):
        is_empty_dir = os.path.isdir(path) and not len(os.listdir(path))
        if not is_empty_dir:
            finish(True, (
                'Can\'t create "%s" (already exists as a non-empty directory)'
            )%path)
    else:
        try:
            os.mkdir(path)
        except BaseException as ex:
            finish(True, 'Can\'t create "%s" (%s)'%(path, str(ex)))

    if command == 'app':
        configuration = {
            'title': arguments.get('--title') or name,
            'icon': arguments.get('--icon') or 'cube'
        }
    
        copy_boilerplate('apps/basic', path)

        with open(os.path.join(path, 'config.ini'), 'r') as app_ini_file:
            app_ini = app_ini_file.read()

        for key, value in configuration.items():
            app_ini = app_ini.replace('{{%s}}'%key, value)
        
        with open(os.path.join(path, 'config.ini'), 'w') as app_ini_file:
            app_ini_file.write(app_ini)
    elif command == 'theme':
        copy_boilerplate('themes/basic', path)
    elif command == 'site':
        do_site_creation(path, name, arguments)
    else:
        raise NotImplementedError()

    print('Created "%s"'%path)

def new():    
    arguments = docopt(new.__doc__)

    name = arguments['<name>']

    command = which_argument(arguments, (
        'site', 'database', 'theme', 'app'
    ))

    if command == 'database':
        do_database_creation(arguments, collected={'database': name})
    else:
        new_filesystem_resource(arguments, command, name)
new.__doc__ = __doc__%(
    describe_options(SITE_CREATION_OPTIONS),
    describe_options(DB_CREATION_OPTIONS)
)
