"""
    zoom api
"""

import logging

import zoom
from zoom.utils import create_csrf_token

logger = logging.getLogger(__name__)


def authenticate(request):
    """API Authentication"""
    logger.debug('api called')

    data = request.data
    username = data.get('username')
    password = data.get('password')

    if username and password:
        site = zoom.get_site()
        user = site.users.first(username=username, status='A')
        if user:
            if user.login(request, password):
                logger.info('%s successfully athenticated to API', username)
                return dict(status='200 OK')
        logger.debug('failed login attempt for %s', username)
    elif username:
        logger.debug('password missing')
    else:
        logger.debug('username missing')

    return zoom.response.JSONResponse(
        dict(
            status='401 Unauthorized'
        ),
        status='401 Unauthorized'
    )


def app(request):
    """API index"""
    if request.data:
        authenticate(request)
    else:
        token = create_csrf_token()
        request.session.csrf_token = token
        return dict(
            status='200 OK',
            csrf_token=token
        )

