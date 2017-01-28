"""
    zoom.session
"""

import logging


import zoom.database


class Session(object):

    def __init__(self, token):
        self.token = token
        self.logger = logging.getLogger(__name__)
        self.logger.debug('load session: %r', token)

    def save(self):
        self.logger.debug('save session: %r', self.token)


def session_handler(request, handler, *rest):
    request.session = Session(request.session_token)
    response = handler(request, *rest)
    request.session.save()
    return response
