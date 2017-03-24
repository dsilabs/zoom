# -*- coding: utf-8 -*-

"""
    zoom.cookies

    The following test is a bit lame because the timestamp makes it tricky to
    test.  Ideally we'd pass in a timer somehow but the cookie module is
    handling the time calculation so without diving into the innards of the
    http.cookies module this is what we have right now.

    >>> cookie = make_cookie()
    >>> add_value(cookie, 'name1', 'value1', 60, True)
    >>> v = get_value(cookie)
    >>> v.startswith('name1=value1; expires=')
    True
    >>> v.endswith('; Secure')
    True
    >>> len(v)
    69
"""

from http.cookies import SimpleCookie
import logging
import uuid


SESSION_COOKIE_NAME = 'zoom_session'
SUBJECT_COOKIE_NAME = 'zoom_subject'
ONE_YEAR = 365 * 24 * 60 * 60


def new_token():
    """generate a new subject ID"""
    return uuid.uuid4().hex


def get_cookies(raw_cookie):
    """extract cookies from raw cookie data"""
    cookie = SimpleCookie(raw_cookie)
    result = dict([(k, cookie[k].value) for k in cookie])
    return result


def make_cookie():
    """construct a cookie"""
    return SimpleCookie()


def add_value(cookie, name, value, lifespan, secure):
    """add a value to a cookie"""
    cookie[name] = value
    cookie[name]['httponly'] = True
    cookie[name]['expires'] = lifespan  # in seconds
    if secure:
        cookie[name]['secure'] = True


def get_value(cookie):
    """get the value portion of a cookie"""
    _, value = str(cookie).split(': ', 1)
    return value


def set_session_cookie(response, session, subject, lifespan, secure=True):
    """construct a session cookie"""
    cookie = make_cookie()
    add_value(cookie, SESSION_COOKIE_NAME, session, lifespan, secure)
    add_value(cookie, SUBJECT_COOKIE_NAME, subject, ONE_YEAR, secure)
    key, value = str(cookie).split(': ', 1)

    # mod_wsgi doesn't like newlines
    value = value.replace('\r', ' ').replace('\n', ' ')

    response.headers[key] = value


def cookie_handler(request, handler, *rest):
    logger = logging.getLogger(__name__)

    cookies = get_cookies(request.cookies)
    request.session_token = cookies.get(SESSION_COOKIE_NAME) or new_token()
    request.subject_token = cookies.get(SUBJECT_COOKIE_NAME) or new_token()
    logger.debug('session token: {}'.format(request.session_token))

    logger.debug('cookies read')

    response = handler(request, *rest)

    set_session_cookie(
        response,
        request.session_token,
        request.subject_token,
        request.session_timeout,
        request.site.secure_cookies,
    )
    logger.debug('cookies set')

    return response
