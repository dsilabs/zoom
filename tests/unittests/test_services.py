"""
    Test the cookies module

"""
# pylint: disable=missing-docstring
# method names are more useful for testing

import unittest

import zoom


class TestServices(unittest.TestCase):
    """test services"""

    def test_run(self):
        message = 'Hello World!'
        result = zoom.services.run('echo "{}"'.format(message))
        self.assertEqual(message + '\n', result)

    def test_run_with_status(self):
        message = 'Hello World!'
        status, stdout, stderr = zoom.services.run(
            'echo "{}"'.format(message),
            returncode=True
        )
        self.assertEqual(0, status)
        self.assertEqual(message + '\n', stdout)
        self.assertEqual('', stderr)

    def test_run_with_error(self):
        message = 'Hello World!'
        status, stdout, stderr = zoom.services.run(
            'cat nada',
            returncode=True
        )
        self.assertEqual(1, status)
        self.assertEqual('', stdout)
        self.assertEqual('cat: nada: No such file or directory\n', stderr)
