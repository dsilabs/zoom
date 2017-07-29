"""
    performance profiler
"""

from decimal import Decimal
import io
import resource
import timeit
import logging
import cProfile
import sys

from zoom.utils import ItemList
from zoom.response import HTMLResponse


def round(value):
    return Decimal(value).quantize(Decimal('1.000'))


class SystemTimer(object):
    """time system events"""

    def __init__(self, start_time=None):
        self.start_time = start_time or timeit.default_timer()
        self.previous_time = self.start_time
        self.record = []
        self.add('modules loaded')

    def add(self, comment):
        """add a measure to the system timer log"""
        def memory_usage_resource():
            rusage_denom = 1024.
            mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / rusage_denom
            return mem
        current_time = timeit.default_timer()
        entry = (
            comment,
            # '.' * (40 - len(comment)),
            round((current_time - self.previous_time) * 1000),
            round((current_time - self.start_time) * 1000),
            round(memory_usage_resource()),
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
        return 'Milestone', 'Time', 'Total', 'Max RSS'


def get_profile_data(profiler):
    save_stdout = sys.stdout
    try:
        sys.stdout = io.StringIO()
        profiler.print_stats()
        result = sys.stdout.getvalue()
    finally:
        sys.stdout = save_stdout
    return result


def handler(request, handler, *rest):
    def send(message):
        if hasattr(request, 'user') and hasattr(request, 'site') and request.site.profiling:
            topic = 'system.debug.%s' % request.user._id
            queue = request.site.queues.topic(topic)
            queue.clear()
            queue.send(message)
            logger.debug('sent profile message to %s', topic)
        else:
            logger.debug('profiler data ignored')

    logger = logging.getLogger(__name__)
    request.profiler = SystemTimer(request.start_time)

    code_profiler = cProfile.Profile()
    code_profiler.enable()

    try:

        result = handler(request, *rest)

    finally:
        code_profiler.disable()
        code_profile = get_profile_data(code_profiler)

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

        if isinstance(result, HTMLResponse):
            send(message)
        else:
            logger.debug('ignoring profile of response type %s', type(result))

        del request.profiler
    return result
