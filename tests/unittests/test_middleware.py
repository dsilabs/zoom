"""
    test middleware
"""

import json
import logging
import unittest

import zoom
from zoom.database import setup_test
from zoom.request import Request
from zoom.sites import Site
from zoom.session import Session
from zoom.middleware import (
    check_csrf,
    display_errors,
    trap_errors,
)

logger = logging.getLogger(__name__)

def noop(_, **__):
    """do nothing handler"""


class TestCSRFMiddleware(unittest.TestCase):
    """test CSRF middleware"""

    def setUp(self):
        self.env = {
            'REQUEST_URI': '/test/route',
            'REQUEST_METHOD': 'POST',
        }
        zoom.system.request = request = Request(self.env)
        request.site = Site()
        request.session = Session(request)
        zoom.forms.form_for('test') # trigger crsf token creation
        self.request = request

    def tearDown(self):
        self.request.session.destroy()

    def test_csrf_token_process(self):
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
        zoom.forms.form_for('test') # keeps same token
        self.assertIs(request.session.csrf_token, token)


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

    def _fail_log_inserts(self):
        db = self.request.site.db
        class FailLogInserts:
            def __call__(inner, *args, **kwargs):
                sql = args[0] if args else ''
                if isinstance(sql, str) and 'insert into log' in sql:
                    raise Exception('dead connection')
                return db(*args, **kwargs)
            def __getattr__(inner, name):
                return getattr(db, name)
        self.request.site.db = FailLogInserts()

    def test_display_errors_when_log_insert_fails(self):
        zoom.system.user.is_admin = True
        self._fail_log_inserts()
        log_handler = zoom.logging.LogHandler(self.request)
        root = logging.getLogger()
        root.addHandler(log_handler)
        try:
            response = display_errors(self.request, throw)
        finally:
            root.removeHandler(log_handler)
        status, headers, content = response.as_wsgi()
        self.assertEqual(status, server_error)
        self.assertTrue(content)
        self.assertTrue(headers)
        self.assertTrue(isinstance(response, zoom.response.HTMLResponse))
        self.assertIn('ouch!', str(content))

    def test_display_errors_json_when_log_insert_fails(self):
        zoom.system.user.is_admin = True
        self.request.env = dict(HTTP_ACCEPT='application/json')
        self._fail_log_inserts()
        log_handler = zoom.logging.LogHandler(self.request)
        root = logging.getLogger()
        root.addHandler(log_handler)
        try:
            response = display_errors(self.request, throw)
        finally:
            root.removeHandler(log_handler)
        self.assertEqual(response.status, server_error)
        self.assertTrue(isinstance(response, zoom.response.JSONResponse))
        self.assertEqual(json.loads(response.content), {
            "message": "ouch!",
            "status": "500 Internal Server Error"
        })


class TestLogInsertFailures(unittest.TestCase):

    def setUp(self):
        def boom(*_args, **_kwargs):
            raise Exception('dead connection')
        request = zoom.request.build('http://localhost')
        request.site = zoom.utils.Bunch(logging=True, db=boom)
        request.app = zoom.utils.Bunch(name='test')
        request.profiler = zoom.profiler.SystemTimer(request.start_time)
        self.request = request

    def test_add_entry_does_not_raise(self):
        zoom.logging.add_entry(self.request, 'E', 'boom')

    def test_trap_errors_when_log_insert_fails(self):
        log_handler = zoom.logging.LogHandler(self.request)
        root = logging.getLogger()
        root.addHandler(log_handler)
        try:
            response = trap_errors(self.request, throw)
        finally:
            root.removeHandler(log_handler)
        status, headers, content = response.as_wsgi()
        self.assertEqual(status, server_error)
        self.assertTrue(content)
        self.assertTrue(headers)
        self.assertTrue(isinstance(response, zoom.response.HTMLResponse))

    def test_complete_log_failure_does_not_kill_response(self):
        def ok(_request):
            return zoom.response.HTMLResponse('ok')
        response = zoom.logging.handler(self.request, ok)
        status, headers, content = response.as_wsgi()
        self.assertEqual(status, '200 OK')
        self.assertEqual(content, b'ok')
