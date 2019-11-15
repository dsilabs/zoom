"""
    test cli
"""

import os
import re
import shutil
import unittest

from subprocess import Popen, PIPE

from zoom.cli import __doc__ as MAIN_USAGE
from zoom.cli.new import new as new_handler

TEST_DIR = os.path.abspath('./_testdata')

def deformat_str(string):
    """Remove whitespace from the given string so it can be compared with or
    as program output across platforms."""
    return re.sub(r'\s+', str(), string)

def agnostic_contains(source, content):
    """Whether the given source contains the given content, agnostic of
    whitespace (which is platform dependent in the context of stdout)."""
    return deformat_str(content) in deformat_str(source)

def invoke(*args, stdin=str(), return_proc=False, **kwargs):
    process = Popen(
        ' '.join(('python3', *args)), 
        shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, 
        **kwargs
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
        code, out, err = invoke('zoom')
        self.assertTrue(code, 'Non-zero exit')
        self.assertTrue(not out, 'No output')
        self.assertTrue(agnostic_contains(err, MAIN_USAGE), 'Usage provided')

    def test_help(self):
        code, out, err = invoke('zoom -h')
        self.assertTrue(not err and not code, 'No error')
        self.assertTrue(agnostic_contains(out, MAIN_USAGE), 'Usage provided')

    def test_command_help(self):
        code, out, err = invoke('zoom -h new')
        self.assertTrue(not err and not code, 'No error')
        self.assertTrue(
            agnostic_contains(out, new_handler.__doc__), 
            'Help provided'
        )

    def test_command_usage_error(self):
        code, out, err = invoke('zoom new invalid command input')
        self.assertTrue(code, 'Non-zero exit')
        self.assertTrue(not out, 'No output')
        self.assertTrue(
            agnostic_contains(new_handler.__doc__, err),
            'Usage provided'
        )

    def test_new_app(self):
        path0 = os.path.join(TEST_DIR, 'app0')
        code, out, err = invoke('zoom new app "%s"'%path0)
        self.assertTrue(not code, 'Process succeeds')
        self.assertTrue(
            os.path.exists(path0) and os.path.isdir(path0), 
            'Parent directory created'
        )
        self.assertTrue(
            os.path.isfile(path0 + '/app.py'), 'Files created'
        )

    def test_pip_install(self):
        lib_path = os.path.join(TEST_DIR, 'libs')
        cwd = os.path.abspath('.')
        os.mkdir(lib_path)
        code, out, err = invoke(
            '-m pip install --target=%s %s'%(lib_path, cwd), 
            cwd=TEST_DIR
        )
        self.assertTrue(not code, 'No error code')

        # Create and environment that will cause our installed Zoom version
        # to be executed.
        child_env = os.environ.copy()
        child_env['PYTHONPATH'] = lib_path

        # Perform a sanity check that we're using the installed version, not
        # this (the repo) one.
        location_check = invoke(
            '-c "import zoom;import os;print(os.path.abspath(zoom.__file__))"',
            env=child_env, cwd=os.path.dirname(cwd)
        )
        self.assertTrue(
            lib_path in location_check[1], 
            'Sanity check; correct lib. path used for child env.'
        )

        # Invoke the installed zoom version to ensure it is linked properly.
        code, out, err = invoke(
            '-m zoom -h', env=child_env, cwd=os.path.dirname(cwd)
        )

        self.assertTrue(
            not code and agnostic_contains(out, MAIN_USAGE), 
            'Module-style invocation works'
        )
