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
        logger.info(str(cookie))

        cookie2 = http.cookies.SimpleCookie()
        cookie2[SESSION_COOKIE_NAME] = 'mysession'
        cookie2[SESSION_COOKIE_NAME]['httponly'] = True
        cookie2[SESSION_COOKIE_NAME]['expires'] = 60
        cookie2[SESSION_COOKIE_NAME]['secure'] = True
        cookie2[SESSION_COOKIE_NAME]['path'] = '/'
        cookie2[SUBJECT_COOKIE_NAME] = 'mysubject'
        cookie2[SUBJECT_COOKIE_NAME]['httponly'] = True
        cookie2[SUBJECT_COOKIE_NAME]['expires'] = 60
        cookie2[SUBJECT_COOKIE_NAME]['secure'] = True
        cookie2[SUBJECT_COOKIE_NAME]['path'] = '/'
        logger.info(str(cookie2))

        self.assertEqual(str(cookie), str(cookie2))

    def test_create_not_secure_cookie(self):
        logger = logging.getLogger('zoom.cookies')

        cookie = http.cookies.SimpleCookie()
        add_value(cookie, SESSION_COOKIE_NAME, 'mysession', 60, False)
        add_value(cookie, SUBJECT_COOKIE_NAME, 'mysubject', 60, False)
        logger.info(str(cookie))

        cookie2 = http.cookies.SimpleCookie()
        cookie2[SESSION_COOKIE_NAME] = 'mysession'
        cookie2[SESSION_COOKIE_NAME]['httponly'] = True
        cookie2[SESSION_COOKIE_NAME]['expires'] = 60
        cookie2[SESSION_COOKIE_NAME]['path'] = '/'
        cookie2[SUBJECT_COOKIE_NAME] = 'mysubject'
        cookie2[SUBJECT_COOKIE_NAME]['httponly'] = True
        cookie2[SUBJECT_COOKIE_NAME]['expires'] = 60
        cookie2[SUBJECT_COOKIE_NAME]['path'] = '/'
        logger.info(str(cookie2))

        self.assertEqual(str(cookie), str(cookie2))
