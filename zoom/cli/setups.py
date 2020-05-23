"""
    zoom setups cli
"""

from argparse import ArgumentParser
import os
import sys

from zoom.cli.utils import legacy_command_argv

def setup():
    """set up a new Zoom instance"""

    join = os.path.join

    parser = ArgumentParser(
        description='set up a new Zoom instance',
        usage='zoom setup [options] directory'
    )

    parser.add_argument('directory', nargs=1)
    args = parser.parse_args(legacy_command_argv('setup'))

    dst = args.directory[0]

    if os.path.exists(dst):
        print('warning: directory exists')
        sys.exit(-1)

    # create the new instance directory
    os.mkdir(dst)

    # create an empty apps directory for new app developement
    os.mkdir(join(dst, 'apps'))

    # create the themes directory for new theme developmenet
    os.mkdir(join(dst, 'themes'))

    # create the default site
    os.mkdir(join(dst, 'sites'))
