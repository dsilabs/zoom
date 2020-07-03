"""
    Test the request module
"""

import http.cookies
import io
import json
import logging
import sys
import unittest

from zoom.request import Request


class TestCGIRequest(unittest.TestCase):
    """test request"""

    def setUp(self):
        self.save_stdin = sys.stdin
        self.server_type = 'cgi'
        self.env = {
            'REQUEST_URI': '/test/route',
        }

    def tearDown(self):
        sys.stdin = self.save_stdin

    def test_server_type(self):
        request = Request(self.env)
        self.assertEqual(request.module, self.server_type)

    def test_get_query_string(self):
        self.env['REQUEST_METHOD'] = 'GET'
        self.env['QUERY_STRING'] = 'name=joe&age=20'
        request = Request(self.env)
        self.assertEqual(request.data, {'name': 'joe', 'age': '20'})

    def test_post_query_string(self):
        payload = 'parameter=value&also=another'
        body = io.BytesIO()
        body.write(payload.encode('utf-8'))
        body.seek(0)
        request = self.get_post_request(body)
        self.env['REQUEST_METHOD'] = 'POST'
        self.env['QUERY_STRING'] = 'name=joe&age=20'
        request = Request(self.env)
        value =  {'age': '20', 'also': 'another', 'name': 'joe', 'parameter': 'value'}
        self.assertEqual(request.data, value)

    def test_route(self):
        request = Request(self.env)
        self.assertEqual(request.route, ['test', 'route'])

    def test_get(self):
        self.env['REQUEST_METHOD'] = 'GET'
        self.env['QUERY_STRING'] = 'parameter=value&also=another'
        request = Request(self.env)
        result = {'also': 'another', 'parameter': 'value'}
        self.assertEqual(request.data, result)

    def test_get_with_duplicates(self):
        env = dict(
            REQUEST_METHOD='GET',
            QUERY_STRING='parameter=one&parameter=two'
        )
        request = Request(env)
        expected = {
            'parameter': ['one', 'two']
        }
        self.assertEqual(request.data, expected)

    def test_get_with_indexed_values(self):
        env = dict(
            REQUEST_METHOD='GET',
            QUERY_STRING='parameter[1]=one&parameter[2]=two'
        )
        request = Request(env)
        expected = {
            'parameter': ['two', 'one'],
        }
        self.assertEqual(sorted(request.data), sorted(expected))

    def get_post_request(self, body):
        sys.stdin = body
        return Request(self.env)

    def test_post(self):
        payload = 'parameter=value&also=another'
        body = io.BytesIO()
        body.write(payload.encode('utf-8'))
        body.seek(0)
        self.env['REQUEST_METHOD'] = 'POST'
        request = self.get_post_request(body)
        result = {'also': 'another', 'parameter': 'value'}
        self.assertEqual(request.data, result)

    def test_data_consumes_body(self):
        payload = 'parameter=value&also=another'
        body = io.BytesIO()
        body.write(payload.encode('utf-8'))
        body.seek(0)
        self.env['REQUEST_METHOD'] = 'POST'
        request = self.get_post_request(body)
        result = {'also': 'another', 'parameter': 'value'}
        self.assertEqual(request.data, result)
        self.assertEqual(request.body, None)

    def test_body(self):
        payload = b'{"title":"Hello World!","body":"This is my first post!"}'
        body = io.BytesIO()
        body.write(payload)
        body.seek(0)
        self.env['REQUEST_METHOD'] = 'POST'
        request = self.get_post_request(body)
        self.assertEqual(request.body.read(), payload)

    def test_body_consumes_data(self):
        payload = b'{"title":"Hello World!","body":"This is my first post!"}'
        body = io.BytesIO()
        body.write(payload)
        body.seek(0)
        request = self.get_post_request(body)
        self.assertEqual(request.body.read(), payload)
        self.assertEqual(request.data, {})

    def test_json_body(self):
        payload = dict(
            title='Hello World!',
            body='This is my first post!'
        )
        body = io.BytesIO()
        body.write(json.dumps(payload).encode('utf-8'))
        body.seek(0)
        request = self.get_post_request(body)
        self.assertEqual(request.json_body, payload)

    def prep_payload(self, payload):
        body = io.BytesIO()
        body.write(payload.encode('utf-8'))
        body.seek(0)
        return body

    def set_payload(self, payload):
        sys.stdin = self.prep_payload(payload)

    def test_delete(self):
        self.env['REQUEST_METHOD'] = 'DELETE'
        self.env['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
        self.set_payload('parameter=value&also=another')
        request = Request(self.env)
        result = {'also': 'another', 'parameter': 'value'}
        self.assertEqual(request.data, result)

    def test_delete_no_body(self):
        self.env['REQUEST_METHOD'] = 'DELETE'
        self.env['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
        self.set_payload('')
        request = Request(self.env)
        result = {}
        self.assertEqual(request.data, result)


class TestWSGIRequest(TestCGIRequest):

    def setUp(self):
        self.save_stdin = sys.stdin
        self.server_type = 'wsgi'
        self.env = {
            'wsgi.version': '1',
            'PATH_INFO': '/test/route',
        }

    def get_post_request(self, body):
        self.env['wsgi.input'] = body
        return Request(self.env)

    def set_payload(self, payload):
        self.env['wsgi.input'] = self.prep_payload(payload)
