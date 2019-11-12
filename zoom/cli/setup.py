"""
    zoom setup cli
"""

from argparse import ArgumentParser
import os
import shutil
import sys

import zoom

def setup(name=None, args=None):
    """set up a new Zoom instance"""

    join = os.path.join

    parser = ArgumentParser(
        description='set up a new Zoom instance',
        usage='zoom setup [options] directory'
    )

    parser.add_argument('directory', nargs=1)
    args = parser.parse_args(args)

    dst = args.directory[0]
    src = zoom.tools.zoompath('web')

    if os.path.exists(dst):
        print('warning: directory exists')
        sys.exit(-1)

    # create the new instance directory
    os.mkdir(dst)

    # create an empty apps directory for new app developement
    os.mkdir(join(dst, 'apps'))

    # create the themes directory for new theme developmenet
    os.mkdir(join(dst, 'themes'))

    # copy default theme
    shutil.copytree(
        join(src, 'themes', 'default'), join(dst, 'themes', 'default')
    )

    # create the default site
    os.mkdir(join(dst, 'sites'))
    shutil.copytree(join(src, 'sites', 'default'), join(dst, 'sites', 'default'))

