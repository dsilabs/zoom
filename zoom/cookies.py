# -*- coding: utf-8 -*-

"""
    zoom.cookies

    The following test is a bit lame because the timestamp makes it tricky to
    test.  Ideally we'd pass in a timer somehow but the cookie module is
    handling the time calculation so without diving into the innards of the
    http.cookies module this is what we have right now.

    >>> cookie = SimpleCookie()
    >>> add_value(cookie, 'name1', 'value1', 60, True)
    >>> v = get_value(cookie)
    >>> v.startswith('name1=value1; expires=')
    True
    >>> v.endswith('; Secure')
    True
    >>> len(v)
    94
    >>> 'SameSite=Strict' in str(v)
    True
    >>> 'Secure' in str(v)
    True
"""

from http.cookies import SimpleCookie, Morsel
import logging
import uuid

import zoom

SESSION_COOKIE_NAME = 'zoom_session'
SUBJECT_COOKIE_NAME = 'zoom_subject'
CSRF_COOKIE_NAME = 'zoom_csrf'

ONE_YEAR = 365 * 24 * 60 * 60

class SameSiteMorsel(Morsel):
    """Add SameSite support for Python 3.7 and older"""
    def add_samesite_support(self):
        if 'samesite' not in self._reserved:
            self._reserved['samesite'] = 'SameSite'


def new_token():
    """generate a new subject ID"""
    return uuid.uuid4().hex


def get_cookies(raw_cookie):
    """extract cookies from raw cookie data"""
    cookie = SimpleCookie(raw_cookie)
    result = dict([(k, cookie[k].value) for k in cookie])
    return result


def add_value(cookie, name, value, lifespan, secure, samesite='Strict'):
    """add a value to a cookie"""
    cookie[name] = value
    cookie[name]['httponly'] = True
    cookie[name]['path'] = '/'
    cookie[name]['expires'] = lifespan  # in seconds
    if secure:
        cookie[name]['secure'] = True

    # for python3.7 and older
    SameSiteMorsel.add_samesite_support(cookie[name])
    cookie[name]['samesite'] = samesite


def get_value(cookie):
    """get the value portion of a cookie"""
    _, value = str(cookie).split(': ', 1)
    return value


def set_session_cookie(response, session, subject, csrf, lifespan, secure=True):
    """construct a session cookie

    >>> import zoom
    >>> response = zoom.response.HTMLResponse('my page')
    >>> set_session_cookie(response, 'sessionid', 'subjectid', 'token', 60)
    >>> 'zoom_session=sessionid' in str(response.cookie)
    True
    >>> 'zoom_csrf=token' in str(response.cookie)
    True
    >>> 'Secure' in str(response.cookie)
    True
    """
    cookie = SimpleCookie()
    add_value(cookie, SESSION_COOKIE_NAME, session, lifespan, secure)
    add_value(cookie, SUBJECT_COOKIE_NAME, subject, ONE_YEAR, secure)
    if csrf:
        add_value(cookie, CSRF_COOKIE_NAME, csrf, lifespan, secure)
    else:
        add_value(cookie, CSRF_COOKIE_NAME, csrf, 0, secure)
    response.cookie = cookie


def handler(request, handler, *rest):
    """Cookie handler

    >>> import zoom
    >>> request = zoom.utils.Bunch(
    ...     cookies=None,
    ...     session_timeout=1,
    ...     site=zoom.sites.Site(),
    ... )
    >>> response = handler(request, lambda a: zoom.response.Response())
    >>> 'zoom_session=' in str(response.cookie)
    True
    """
    logger = logging.getLogger(__name__)

    cookies = get_cookies(request.cookies)
    request.session_token = cookies.get(SESSION_COOKIE_NAME) or new_token()
    request.subject_token = cookies.get(SUBJECT_COOKIE_NAME) or new_token()
    request.csrf_token = cookies.get(CSRF_COOKIE_NAME)
    request.form_token = None

    logger.debug('cookies read')
    logger.debug('form_token: %s csrf_token: %s', request.form_token, request.csrf_token)

    response = handler(request, *rest)

    logger.debug('form_token: %s csrf_token: %s', request.form_token, request.csrf_token)

    set_session_cookie(
        response,
        request.session_token,
        request.subject_token,
        request.form_token or request.csrf_token,
        request.session_timeout,
        request.site.secure_cookies,
    )

    return response
