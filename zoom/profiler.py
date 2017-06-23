"""
    performance profiler
"""

from decimal import Decimal
import resource
import timeit

from zoom.utils import ItemList
from zoom.page import page


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
        def round(value):
            return Decimal(value).quantize(Decimal('1.000'))
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


def handler(request, handler, *rest):
    def send(message):
        if hasattr(request, 'user') and hasattr(request, 'site') and request.site.profiling:
            topic = 'system.debug.%s' % request.user._id
            queue = request.site.queues.topic(topic)
            queue.clear()
            queue.send(message)

    request.profiler = SystemTimer(request.start_time)
    try:
        result = handler(request, *rest)
    finally:
        request.profiler.add('finished')

        # TODO: move this to a debug layer that sends other things to the debugger
        message = dict(
            profiler=request.profiler.record,
            profiler_path=request.path,
        )
        if isinstance(result, page):
            send(message)

        del request.profiler
    return result
