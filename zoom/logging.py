"""
    zoom.logging
"""

import logging

from zoom.context import context
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
        'admin', #TODO: get actual app
        request.path,
        status,
        hasattr(request, 'user') and request.user._id or None,
        request.ip_address,
        request.remote_user,
        request.host,
        now(),
        int(float(request.get_elapsed()) * 1000),
        entry,
    )


def log_activity(message, *args, **kwargs):
    # I think this should actually be a verb of some sort but I am
    # drawing a blank at this moment of what to call it. :/
    add_entry(context.request, 'A', message, *args, **kwargs)


class LogHandler(logging.Handler):

    def __init__(self, request, level=logging.INFO):
        logging.Handler.__init__(self, level)
        self.request = request

    def emit(self, record):
        entry = self.format(record)
        status = record.levelname[0]
        add_entry(self.request, status, entry)


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
        request.profiler.time('log request', add_entry, request, 'C', 'complete')
        remove_log_handler(log_handler)
    return result
