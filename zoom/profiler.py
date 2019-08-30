"""
    performance profiler
"""

from decimal import Decimal
import io
import timeit
import logging
import cProfile
import os
import sys

from zoom.utils import ItemList
from zoom.response import HTMLResponse


def round(value):
    """Round a decimal value

    >>> round(Decimal(1.23422))
    Decimal('1.234')
    """
    return Decimal(value).quantize(Decimal('1.000'))


class SystemTimer(object):
    """time system events

    >>> timer = SystemTimer()
    >>> timer.add('got here')
    >>> timer.add('got there')

    >>> import time
    >>> timer.time('slow step', time.sleep, 0.1)

    >>> report = timer.report()
    >>> len(report.splitlines())
    7

    >>> len(timer.data)
    5
    """

    def __init__(self, start_time=None):
        self.start_time = start_time or timeit.default_timer()
        self.previous_time = self.start_time
        self.record = []
        self.add('modules loaded')

    def add(self, comment):
        """add a measure to the system timer log"""
        current_time = timeit.default_timer()
        entry = (
            comment,
            # '.' * (40 - len(comment)),
            round((current_time - self.previous_time) * 1000),
            round((current_time - self.start_time) * 1000),
        )
        self.record.append(entry)
        self.previous_time = current_time

    def time(self, name, function, *args, **kwargs):
        self.add('starting {}'.format(name))
        result = function(*args, **kwargs)
        self.add('finished {}'.format(name))
        return result

    def report(self):
        """print a report of the timed events"""
        return str(ItemList(self.data, labels=self.labels))

    @property
    def data(self):
        return self.record

    @property
    def labels(self):
        return 'Milestone', 'Time', 'Total'


def get_profile_data(profiler):
    """Capture the stdout printout of the code profiler

    >>> class Profiler(object):
    ...     def print_stats(self):
    ...         print('the stats!')
    >>> get_profile_data(Profiler())
    'the stats!\\n'
    """
    save_stdout = sys.stdout
    try:
        sys.stdout = io.StringIO()
        profiler.print_stats()
        result = sys.stdout.getvalue()
    finally:
        sys.stdout = save_stdout
    return result


def profiled(request, handler, *rest):
    def send(message):
        if hasattr(request, 'user') and hasattr(request, 'site') and request.site.profiling:
            topic = 'system.debug.%s' % request.user._id
            queue = request.site.queues.topic(topic)
            queue.clear()
            queue.send(message)
            logger.debug('sent profile message to %s', topic)
        else:
            logger.debug('profiler data ignored')
            if not hasattr(request, 'user'):
                logger.debug('profile user missing')
            if not hasattr(request, 'site'):
                logger.debug('profile site missing')
            elif not request.site.profiling:
                logger.debug('profiling turned off')


    profiling_code = request.env.get('ZOOM_CODE_PROFILER')


    logger = logging.getLogger(__name__)

    if profiling_code:
        code_profiler = cProfile.Profile()
        code_profiler.enable()

    try:

        result = handler(request, *rest)

    finally:
        if profiling_code:
            code_profiler.disable()
            code_profile = get_profile_data(code_profiler)
        else:
            code_profile = 'code profiler is off'

        request.profiler.add('finished')

        # TODO: move this to a debug layer that sends other things to the debugger
        message = dict(
            profiler_path=request.path,
            system_profile=request.profiler.record,
            database_profile=['no database'],
            code_profile=code_profile,
        )
        if hasattr(request, 'site'):
            if hasattr(request.site, 'db'):
                message['database_profile'] = [(
                    round(time * 1000),
                    statement,
                    values,
                    source,
                ) for time, statement, values, source in request.site.db.get_stats()]

        result = locals().get('result', None)

        # Retrieve headers from the result if it has that property.
        headers = getattr(result, 'headers', dict())
        if not isinstance(headers, dict):
            # Handle the case where the response class is doing something
            # funky with its headers object.
            logger.debug("headers isn't a dict, won't profile")
            headers = dict()
        # Transform headers to lower case because casing isn't invariant.
        headers = {k.lower(): v for k, v in headers.items()}
        # Profile if this is an HTML response.
        if 'html' in headers.get('content-type', str()):
            send(message)
        else:
            logger.debug('ignoring profile of response type %s', type(result))

        del request.profiler
    return result


def handler(request, handler, *rest):
    """Handle profiled requests"""

    if os.environ.get('ZOOM_PROFILER'):
        request.profiling = True
        return profiled(request, handler, *rest)
    else:
        return handler(request, *rest)
