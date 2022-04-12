"""
    test middleware
"""

import json
import logging
import unittest

import zoom
from zoom.database import setup_test
from zoom.request import Request
from zoom.site import Site
from zoom.session import Session
from zoom.middleware import (
    check_csrf,
    display_errors
)

logger = logging.getLogger(__name__)

def noop(_, **__):
    """do nothing handler"""


# class TestCSRFMiddleware(unittest.TestCase):
#     """test CSRF middleware"""

#     def setUp(self):
#         self.env = {
#             'REQUEST_URI': '/test/route',
#             'REQUEST_METHOD': 'POST',
#         }
#         zoom.system.request = request = Request(self.env)
#         request.site = Site(request)
#         request.site.db = setup_test()
#         request.session = Session(request)
#         zoom.forms.form_for('test')
#         # token = forms.csrf_token()  # trigger crsf token creation
#         self.request = request

#     def tearDown(self):
#         self.request.session.destroy()

#     def test_csrf_token_process(self):
#         request = self.request
#         self.assertEqual(request.method, 'POST')
#         self.assertEqual(request.site.csrf_validation, True)  # ensure default is to be enabled
#         token =
#         # self.assertIsNotNone(getattr(request.session, 'csrf_token', None))

#     def test_check_csrf(self):
#         request = self.request
#         token = request.session.csrf_token
#         request.body_consumed = True
#         request.data_values = dict(csrf_token=token)
#         check_csrf(request, noop)
#         self.assertIsNotNone(getattr(request.session, 'csrf_token', None))
#         zoom.forms.form_for('test') # generates a new token
#         self.assertIsNot(request.session.csrf_token, token)


def throw(request):
    raise Exception('ouch!')

def forbid(request):
    raise zoom.exceptions.UnauthorizedException('forbidden!')

server_error = '500 Internal Server Error'
forbidden = '403 Forbidden'

class TestDisplayError(unittest.TestCase):

    def setUp(self):
        request = zoom.request.build('http://localhost')
        request.app = zoom.utils.Bunch(theme='default', templates_paths=[])
        request.host = 'localhost'
        request.site = zoom.sites.Site()
        request.site.theme = 'default'
        request.site.request = request
        self.request = request
        zoom.system.request = request
        zoom.system.site = request.site
        zoom.system.user = request.site.users.first(username='admin')
        zoom.system.providers = []

    def test_display_error_as_admin(self):
        zoom.system.user.is_admin = True
        response = display_errors(self.request, throw)
        self.assertTrue(isinstance(response, zoom.response.HTMLResponse))

    def test_display_error_as_non_admin(self):
        zoom.system.user.is_admin = False
        response = display_errors(self.request, throw)
        self.assertEqual(response.status, server_error)
        self.assertTrue(isinstance(response, zoom.response.HTMLResponse))

    def test_error_status_500_html(self):
        zoom.system.user.is_admin = False
        response = display_errors(self.request, throw)
        self.assertEqual(response.status, server_error)
        self.assertTrue(isinstance(response, zoom.response.HTMLResponse))

    def test_unauthorized(self):
        zoom.system.user.is_admin = False
        response = display_errors(self.request, forbid)
        self.assertEqual(response.status, forbidden)
        self.assertTrue(isinstance(response, zoom.response.HTMLResponse))

    def test_error_status_500_json(self):
        zoom.system.user.is_admin = True
        self.request.env = dict(HTTP_ACCEPT='application/json') # mock
        response = display_errors(self.request, throw)
        self.assertEqual(response.status, server_error)
        self.assertTrue(isinstance(response, zoom.response.JSONResponse))
        self.assertEqual(json.loads(response.content), {
            "message": "ouch!",
            "status": "500 Internal Server Error"
            }
        )
