# -*- coding: utf-8 -*-

"""
    zoom CLI

    Zoom command line utility.
"""

# pylint: disable=unused-argument

import os
import time
import shlex
from optparse import OptionParser

from subprocess import Popen, PIPE
from os.path import exists

__all__ = [
    'server',
]


def server(instance='.'):
    """run an instance using Python's builtin HTTP server"""

    parser = OptionParser(usage='usage: %prog server [options] instance')
    parser.add_option("-p", type="int", dest="port", default=8000, help='service port')
    (options, args) = parser.parse_args()

    if len(args) > 2:
        parser.error('incorrect number of arguments')
    elif len(args) == 2:
        instance = args[1]
    else:
        instance = instance

    print('starting server for {} on port {}'.format(instance, options.port))

    from zoom.server import run as runweb
    runweb(port=options.port, instance=instance)
    print('\rstopped')


