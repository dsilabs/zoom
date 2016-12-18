"""
    Test the request module
"""

import unittest
import http.cookies
import logging

from zoom.request import Request


class TestCGIRequest(unittest.TestCase):
    """test request"""

    def setUp(self):
        self.server_type = 'cgi'
        self.env = {
            'REQUEST_URI': '/test/route',
        }

    def test_server_type(self):
        request = Request(self.env)
        self.assertEqual(request.module, self.server_type)

    def test_query_string(self):
        self.env['QUERY_STRING'] = 'name=joe&age=20'
        request = Request(self.env)
        self.assertEqual(request.data, {'name': 'joe', 'age': '20'})

    def test_route(self):
        request = Request(self.env)
        self.assertEqual(request.route, ['test', 'route'])


class TestWSGIRequest(TestCGIRequest):

    def setUp(self):
        self.server_type = 'wsgi'
        self.env = {
            'wsgi.version': '1',
            'PATH_INFO': '/test/route',
        }
