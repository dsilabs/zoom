"""
    zoom.logging
"""

import logging

import zoom

cmd = """
    insert into log (
        app, path, status, user_id, address,
        login, server, timestamp, elapsed, message
    ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
"""


def add_entry(request, status, entry):
    """Add an entry to the system log"""
    if request.site.logging:
        request.site.db(
            cmd,
            hasattr(request, 'app') and request.app.name or None,
            request.path,
            status,
            hasattr(request, 'user') and request.user._id or None,
            request.ip_address,
            request.remote_user,
            request.host,
            zoom.tools.now(),
            int(request.elapsed * 1000),
            entry,
        )


def log_activity(message, *args, **kwargs):
    """Log user activity

    Use for high level user activity logging, such as editing records.
    """
    add_entry(zoom.system.request, 'A', message, *args, **kwargs)


class LogHandler(logging.Handler):
    """Log handler

    Logs information to the log table in the system database.
    """

    def __init__(self, request, level=logging.INFO):
        logging.Handler.__init__(self, level)
        self.request = request

    def emit(self, record):
        entry = self.format(record)
        status = record.levelname[0]
        add_entry(self.request, status, entry)


def handler(request, handler, *rest):
    """Handles logging"""
    root_logger = logging.getLogger()

    log_handler = LogHandler(request)
    root_logger.addHandler(log_handler)
    try:
        result = handler(request, *rest)
    finally:
        request.profiler.time('log request', add_entry, request, 'C', 'complete')
        root_logger.removeHandler(log_handler)
    return result
