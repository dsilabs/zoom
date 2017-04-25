"""
    zoom.logging
"""

import logging

from zoom.tools import now

cmd = """
    insert into log (
        app, path, status, user_id, address,
        login, server, timestamp, elapsed, message
    ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
"""


def add_entry(request, status, entry):
    db = request.site.db
    db(cmd,
        'admin',
        request.path,
        status,
        request.user._id,
        request.ip_address,
        request.remote_user,
        request.host,
        now(),
        int(float(request.get_elapsed()) * 100),
        entry,
    )


class LogHandler(logging.Handler):

    def __init__(self, request, level=logging.INFO):
        logging.Handler.__init__(self, level)
        self.request = request

    def emit(self, record):
        entry = self.format(record)
        add_entry(self.request, 'I', entry)


def add_log_handler(request):
    log_handler = LogHandler(request)
    logger = logging.getLogger()
    logger.addHandler(log_handler)

    logger = logging.getLogger(__name__)
    logger.debug('added log handler')
    return log_handler


def remove_log_handler(log_handler):
    logger = logging.getLogger(__name__)
    logger.debug('removing log handler')

    logger = logging.getLogger()
    logger.removeHandler(log_handler)



def handler(request, handler, *rest):
    log_handler = add_log_handler(request)
    try:
        result = handler(request, *rest)
    finally:
        add_entry(request, 'C', 'complete')
        remove_log_handler(log_handler)
    return result
