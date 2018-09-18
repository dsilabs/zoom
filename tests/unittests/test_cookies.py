"""
    Test the cookies module

"""
# pylint: disable=missing-docstring
# method names are more useful for testing

import unittest
import http.cookies
import logging

from zoom.cookies import (
    add_value,
    SESSION_COOKIE_NAME,
    SUBJECT_COOKIE_NAME,
)


class TestCookies(unittest.TestCase):
    """test system cookies"""

    def test_create_cookie(self):
        logger = logging.getLogger('zoom.cookies')

        cookie = http.cookies.SimpleCookie()
        add_value(cookie, SESSION_COOKIE_NAME, 'mysession', 60, True)
        add_value(cookie, SUBJECT_COOKIE_NAME, 'mysubject', 60, True)
        cookie = str(cookie)
        logger.info(cookie)

        self.assertIn('Set-Cookie:', cookie)
        self.assertIn('zoom_session=mysession', cookie)
        self.assertIn('expires=', cookie)
        self.assertIn('HttpOnly', cookie)
        self.assertIn('Path=/', cookie)
        self.assertIn('Secure', cookie)


    def test_create_not_secure_cookie(self):
        logger = logging.getLogger('zoom.cookies')

        cookie = http.cookies.SimpleCookie()
        add_value(cookie, SESSION_COOKIE_NAME, 'mysession', 60, False)
        add_value(cookie, SUBJECT_COOKIE_NAME, 'mysubject', 60, False)
        cookie = str(cookie)
        logger.info(cookie)

        self.assertIn('Set-Cookie:', cookie)
        self.assertIn('zoom_session=mysession', cookie)
        self.assertIn('expires=', cookie)
        self.assertIn('HttpOnly', cookie)
        self.assertIn('Path=/', cookie)
        self.assertNotIn('Secure', cookie)
