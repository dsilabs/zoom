"""
    zoom.user
"""

import logging


class User(object):

    def __init__(self, username):
        self.username = username
        logger = logging.getLogger(__name__)
        logger.debug('user loaded: %r', username)


def user_handler(request, handler, *rest):
    request.user = User(request.remote_user)
    return handler(request, *rest)
