"""
    Test the request module
"""

import unittest
import http.cookies
import logging

from zoom.request import Request


class TestRequest(unittest.TestCase):
    """test request"""

    def test_server_type(self):
        env = {}
        request = Request(env)
        self.assertEqual(request.module, 'cgi')

        env = {
            'wsgi.version': '1',
            }
        request = Request(env)
        self.assertEqual(request.module, 'wsgi')
