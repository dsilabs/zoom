"""
    zoom setup cli
"""

from argparse import ArgumentParser
import os
import shutil
import sys

def setup(name=None):
    """set up a new Zoom instance"""

    join = os.path.join

    parser = ArgumentParser(
        description='set up a new Zoom instance',
        usage='zoom setup [options] directory'
        )

    parser.add_argument('directory', nargs=1)
    args = parser.parse_args()

    if os.path.exists(args.directory[0]):
        print('warning: directory exists')
        sys.exit(-1)

    # locate the bundled work area
    src = os.path.abspath(
        os.path.join(os.path.split(__file__)[0], '../../web'),
    )

    # create the new directory
    dst = args.directory[0]
    os.mkdir(dst)

    # create an empty apps directory for new app developement
    os.mkdir(join(dst, 'apps'))

    # create the themes directory for new theme developmenet
    os.mkdir(join(dst, 'themes'))
    # copy default theme
    shutil.copytree(
        join(src, 'themes', 'default'), join(dst, 'themes', 'default')
    )

    # copy sites directory
    shutil.copytree(join(src, 'sites'), join(dst, 'sites'))


