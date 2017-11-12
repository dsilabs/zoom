"""
    Test the CSRF middleware
"""
import logging
import unittest

import zoom
from zoom.database import setup_test
from zoom.request import Request
from zoom.site import Site
from zoom.session import Session
from zoom.middleware import check_csrf, reset_csrf_token


logger = logging.getLogger(__name__)

def noop(request, **rest):
    """do nothing handler"""
    pass


class TestCSRFMiddleware(unittest.TestCase):
    """test CSRF middleware"""

    def setUp(self):
        self.env = {
            'REQUEST_URI': '/test/route',
            'REQUEST_METHOD': 'POST',
        }
        zoom.system.providers = []
        request = Request(self.env)
        request.site = Site(request)
        request.site.db = setup_test()
        request.session = Session(request)
        reset_csrf_token(request.session)  # bind a token
        self.request = request

    def tearDown(self):
        self.request.session.destroy()

    def test_csrf_token_process(self):
        """test whether the request and site are setup to process the csrf token"""
        request = self.request
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.site.csrf_validation, True)  # ensure default is to be enabled
        self.assertIsNotNone(getattr(request.session, 'csrf_token', None))

    def test_check_csrf(self):
        request = self.request
        token = request.session.csrf_token
        request.body_consumed = True
        request.data_values = dict(csrf_token=token)
        check_csrf(request, noop)
        self.assertIsNotNone(getattr(request.session, 'csrf_token', None))
        self.assertIsNot(request.session.csrf_token, token)
