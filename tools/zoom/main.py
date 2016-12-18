# -*- coding: utf-8 -*-

"""
    zoom

    Zoom command line utility
"""

import sys
import inspect
from argparse import ArgumentParser

from zoom.utils import ItemList

import commands


class SimpleException(Exception):
    """an exception that traps everything"""
    pass


def get_functions():
    """get a dictionary containing the valid command functions"""
    functions = {
        command: getattr(commands, command) for
        command in dir(commands) if command in commands.__all__
    }
    return functions


def dispatch(args):
    """dispatch a command for running"""
    functions = get_functions()
    cmd = args[1]
    if cmd in functions:
        del sys.argv[1]
        functions[cmd]()
    else:
        raise Exception('No such command %s' % cmd)


def list_commands():
    """print lits of valid commands to stdout"""
    result = ItemList([('command', 'purpose', 'usage')])
    for name, function in sorted(get_functions().items()):
        if not name.startswith('_'):
            doc = function.__doc__
            argspec = inspect.getargspec(function)
            sig = ['zoom {} [<options>]'.format(name)]
            sig.extend(['<{}>'.format(arg)
                        for arg in argspec.args if arg != 'options'])
            if argspec.varargs:
                sig.append('[{}...]'.format(argspec.varargs))
            sig = ' '.join(sig)
            result.append([name, doc, sig])
    print(result)


def main():
    """main program

    calls the appropriate method corresponding to the command line args
    """

    if len(sys.argv) == 2 and sys.argv[-1] in ['-h', '--help']:
        parser = ArgumentParser(
            description='zoom command line utility',
            usage='zoom <command> [options] [arguments]\n'
                  '       zoom <command> -h'
            )
        parser.add_argument('command', nargs='?')
        args = parser.parse_args()

    try:
        if len(sys.argv) > 1:
            dispatch(sys.argv)
        else:
            list_commands()

    except SimpleException as msg:
        print('fatal: %s' % msg)


if __name__ == '__main__':
    main()
