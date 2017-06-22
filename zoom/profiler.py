"""
    performance profiler
"""

import timeit
from zoom.utils import ItemList

class SystemTimer(object):
    """time system events"""

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
            (current_time - self.previous_time) * 1000,
            (current_time - self.start_time) * 1000,
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


def handler(request, handler, *rest):
    request.profiler = SystemTimer(request.start_time)
    try:
        result = handler(request, *rest)
    finally:
        request.profiler.add('finished')
        print(request.profiler.report())
        del request.profiler
    return result
