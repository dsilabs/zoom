"""
    zoom.session
"""

import logging


import zoom.database


class Session(object):

    def __init__(self, token):
        self.token = token
        logger = logging.getLogger(__name__)
        logger.debug('session token: %r', token)


def session_handler(request, handler, *rest):
    request.session = Session(request.session_token)
    return handler(request, *rest)
