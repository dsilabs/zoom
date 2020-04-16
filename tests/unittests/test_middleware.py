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
from zoom.middleware import (
    check_csrf,
    display_errors
)
from zoom.render import apply_helpers, add_helpers

error_message = """
    <div class="jumbotron">
        <h1>Whoops!</h1>
        <p>Something went wrong!</p>
        <p>Please try again later or contact {{owner_link}} for assistance.<p>
    </div>
 """

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
        zoom.system.request = request = Request(self.env)
        request.site = Site(request)
        request.site.db = setup_test()
        request.session = Session(request)
        zoom.forms.form_for('test') # trigger crsf token creation
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
        zoom.forms.form_for('test') # generates a new token
        self.assertIsNot(request.session.csrf_token, token)


def throw(request):
    raise Exception('ouch!')


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
        zoom.system.user.is_admin = False
        message = 'Something is broken'
        response = display_errors(self.request, throw)
        self.assertTrue(isinstance(response, zoom.response.HTMLResponse))
        body = zoom.render.render(response.content, content=message)
        self.assertIn(message, body)

