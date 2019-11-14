"""
    test cli
"""

import os
import re
import shutil
import unittest

from subprocess import Popen, PIPE
from requests import get

from zoom.cli import __doc__ as MAIN_USAGE
from zoom.cli.new import new as new_handler

TEST_DIR = os.path.abspath('./_testdata')

def deformat_str(string):
    """Remove whitespace from the given string so it can be compared with or
    as program output across platforms."""
    return re.sub(r'\s+', str(), string)

def agnostic_contains(output, content):
    return deformat_str(content) in deformat_str(output)

def invoke(*args, stdin=str(), return_proc=False):
    process = Popen(
        ' '.join(('python zoom', *args)), shell=True, 
        stdin=PIPE, stdout=PIPE, stderr=PIPE
    )
    if return_proc:
        return process
    out, err = process.communicate(stdin)

    return process.returncode, out.decode(), err.decode()

class TestCLI(unittest.TestCase):
    
    def setUp(self):
        try:
            shutil.rmtree(TEST_DIR)
        except: pass
        os.mkdir(TEST_DIR)

    def tearDown(self):
        shutil.rmtree(TEST_DIR)

    def test_usage(self):
        code, out, err = invoke()
        self.assertTrue(code, 'Non-zero exit')
        self.assertTrue(not out, 'No output')
        self.assertTrue(agnostic_contains(err, MAIN_USAGE), 'Usage provided')

    def test_help(self):
        code, out, err = invoke('-h')
        self.assertTrue(not err and not code, 'No error')
        self.assertTrue(agnostic_contains(out, MAIN_USAGE), 'Usage provided')

    def test_command_help(self):
        code, out, err = invoke('-h new')
        self.assertTrue(not err and not code, 'No error')
        self.assertTrue(agnostic_contains(out, new_handler.__doc__), 'Help provided')

    def test_command_usage_error(self):
        code, out, err = invoke('new invalid command input')
        self.assertTrue(code, 'Non-zero exit')
        self.assertTrue(not out, 'No output')
        self.assertTrue(agnostic_contains(new_handler.__doc__, err), 'Usage provided')

    def test_new_app(self):
        path0 = os.path.join(TEST_DIR, 'app0')
        code, out, err = invoke('new app "%s"'%path0)
        self.assertTrue(not code, 'Process succeeds')
        self.assertTrue(os.path.exists(path0) and os.path.isdir(path0), 'Parent directory created')
        self.assertTrue(os.path.isfile(path0 + '/app.py'), 'Files created')

    def test_server(self):
        server_proc = invoke('server -p 7999', return_proc=True)
        try:
            get('http://localhost:7999')
        except:
            self.assertTrue(False, 'Server responds')
        
        server_proc.kill()
        # Dispatch another request so server_proc stops blocking and catches the SIGKILL.
        get('http://localhost:7999')
