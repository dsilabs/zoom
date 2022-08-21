"""
    apptest

    tools for writing application integration tests
"""
# pragma: nocover

import logging
import os
import unittest

import zoom
import zoom.middleware as middleware

from zoom.testing.common import get_output_path


def get_path():
    default_test_path = zoom.tools.zoompath('zoom', '_assets', 'web', 'sites', 'localhost')
    path = os.environ.get('ZOOM_TEST_PATH', default_test_path)
    return path


class AppTestPrimitives(unittest.TestCase):
    """AppTest Primitives"""

    logger = logging.getLogger(__name__)
    response = None
    cookies = None
    session_token = None
    subject_token = None
    request = None
    redirected = False
    path = get_path()

    name = property(lambda a: os.path.dirname(a.path))
    url = property(lambda a: 'http://'+os.path.basename(a.path))
    base_url = ''

    def setUp(self):
        self.site = zoom.sites.Site(self.path)

    def tearDown(self):
        del self.site

    def handle(self, request):
        handlers = (
            middleware.zoom.request.handler,
            middleware.reset_modules,
            middleware.capture_stdout,
            middleware.zoom.site.handler,
            middleware.serve_themes,
            middleware.zoom.database.handler,
            middleware.zoom.queues.handler,
            middleware.zoom.models.handler,
            middleware.zoom.logging.handler,
            middleware.zoom.session.handler,
            middleware.zoom.component.handler,
            # # middleware.check_csrf,
            middleware.zoom.users.handler,
            middleware.zoom.render.handler,
            middleware.display_errors,
            middleware.zoom.apps.handler,
            middleware.not_found,
        )
        response = middleware.handle(request, handlers)

        self.session_token = request.session_token
        self.subject_token = request.subject_token

        self.logger.info('%s - %.0fms', request.path, request.elapsed * 1000)
        self.logger.debug('\n\n')
        return response

    def build_request(self, url=None, data=None):
        """build a request"""
        if isinstance(url, str) and url.startswith(self.url):
            request_url = url
        else:
            request_url = self.url + self.base_url + (url or '/')

        instance_path = os.path.dirname(os.path.dirname(self.site.path))
        request = zoom.request.build(
            request_url,
            data or {},
            instance_path,
        )
        request.site_path = self.site.path
        request.ip_address = '127.0.0.1'

        request.session_token = self.session_token
        request.subject_token = self.subject_token

        return request

    def get(self, url=None):
        """get a response"""
        self.request = self.build_request(url)
        self.response = self.handle(self.request)
        self.clear()
        return self.response

    def post(self, url=None, data=None):
        """get a response"""
        self.redirected = False
        self.request = request = self.build_request(url, data)
        self.response = self.handle(request)
        self.clear()
        if self.response.status in ['302 Found']:
            url = self.response.headers.get('Location')
            if url:
                redirected_response = self.get(url)
                self.redirected = url
                return redirected_response
            else:
                raise Exception('redirect location missing')
        return self.response

    def save_content(self, filename=None):
        """Save page content to a file

        If filename is provided, the page content will be saved to that
        locatino.  If not the content will be saved to the tests/output
        directory in a filename starting with "content-", followed by
        the test name, followed by a ".html" extension.

        This function can be called anytime you wish to see the content
        of the current page.  It is called automatically whenever a
        test fails due to missing content.
        """
        if filename is None:

            join = os.path.join
            test_output_directory = get_output_path()
            if not os.path.isdir(test_output_directory):
                os.mkdir(test_output_directory)

            test_name = unittest.TestCase.id(self)
            filename = join(
                test_output_directory,
                'content-%s.html' % test_name
            )

        print('saving content to %s' % filename)
        with open(filename, 'w') as f:
            f.write(str(self.response.content))

    def contains(self, text):
        """return True if response contains text"""
        return text in self.response.content

    def url_matches(self, location, target):
        return (
            location == target or (
            location == self.url + self.base_url + target
            )
        )

    def assertRedirectResponse(self, location=None):
        """Pass if response is a redirect"""
        status = self.response.status
        if status not in ['302 Found']:
            raise AssertionError('expected Redirect but got %r' % status)
        url = self.response.headers.get('Location')
        if location and not self.url_matches(url, location):
            msg = 'redirect location is %r instead of %r as expected'
            raise AssertionError(msg % (url, location))

    def assertNotRedirectResponse(self, location=None):
        """Pass if response is a redirect"""
        status = self.response.status
        if location is None and status in ['302 Found']:
            raise AssertionError('unexpected redirect')
        url = self.response.headers.get('Location')
        if location is not None and self.url_matches(url, location):
            msg = 'redirect location is %r'
            raise AssertionError(msg % url)

    def assertContains(self, text):
        """Pass if response contains text"""
        if not self.contains(text):
            self.save_content()
            raise AssertionError(
                '%s object does not contain %r' % (
                    type(self.response),
                    text
                )
            )

    def assertNotContains(self, text):
        """Pass if response does not contain text"""
        if self.contains(text):
            self.save_content()
            raise AssertionError('response contains %r' % text)

    def assertReturnStatus(self, code):
        """Pass if return status is as expected"""
        try:
            if isinstance(code, str):
                self.assertEqual(self.response.status, code)
            else:
                self.assertEqual(int(self.response.status[:3]), code)
        except Exception:
            raise AssertionError(
                'expected return status %r but got %r' % (
                    code, self.response.status))

    def assertRedirected(self, location=None):
        if not self.redirected:
            raise AssertionError('not redirected as expected')
        if location and not self.url_matches(self.redirected, location):
            msg = 'redirected to %r instead of %r as expected'
            raise AssertionError(msg % (self.redirected, location))

    def assertNotRedirected(self):
        if self.redirected:
            raise AssertionError('redirected when not expected')

    def click(self, name):
        self.assertContains(name)
        if name.endswith('_button'):
            return self.press(name)
        return self.get('/'.join([self.request.path, name]))

    def fill(self, data):
        self.request = self.build_request(self.request.path, data)

    def clear(self):
        """Clear the request of form data"""
        self.request = self.build_request(self.request.path)

    def press(self, name):
        self.assertContains(name)
        self.request.data[name] = name
        self.redirected = False
        # print('posting to', self.request.path, self.request.data)
        self.response = self.handle(self.request)
        self.clear()
        if self.response.status in ['302 Found']:
            url = self.response.headers.get('Location')
            if url:
                # print('redirecting to %r' % url)
                self.get(url)
                self.redirected = url
                # return redirected_response
            else:
                raise Exception('redirect location missing')
        else:
            if self.response.status == '200 OK':
                # usually a validation error so dump the page content for analysis
                self.save_content()
            raise Exception('redirect missing %r' % self.response.status)
        return self.response

class AppTestCase(AppTestPrimitives):
    """App test base class"""

    credentials = {
        'admin': 'admin',
        'user': 'user',
    }
    username = None

    def setUp(self):
        AppTestPrimitives.setUp(self)
        self.logout()
        if self.username:
            self.as_user(self.username)

    def login(self, username, password):
        self.post(
            '/login',
            dict(
                username=username,
                password=password,
                login_button='Login'
            )
        )

    def logout(self):
        self.get()
        if self.contains('/logout'):
            self.get('/logout')

    def as_user(self, username):
        self.logout()
        if username in self.credentials:
            self.login(username, self.credentials[username])
        else:
            raise Exception('test username {!r} unknown'.format(username))
