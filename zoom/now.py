"""
    zoom._now

    provides "live" date and time properties
"""

import sys
import datetime


one_day = datetime.timedelta(1)
one_week = one_day * 7
one_hour = datetime.timedelta(hours=1)
one_minute= datetime.timedelta(minutes=1)

class Now(object):
    """Provide values related to current time"""

    @property
    def now(self):
        return datetime.datetime.now()

    @property
    def today(self):
        return datetime.date.today()

    @property
    def yesterday(self):
        return datetime.date.today() - one_day

    @property
    def tomorrow(self):
        return datetime.date.today() + one_day

sys.modules['_now'] = Now()
from _now import now

# now = _now.now
