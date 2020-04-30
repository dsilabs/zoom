"""

    sample background process

    This module runs a background process and provides the page where
    the results of that background process can be viewed.

"""


import zoom
from zoom.background import cron


class SampleAppTickEvent(zoom.Record):

    @property
    def when(self):
        return zoom.helpers.when(self.timestamp)

Event = SampleAppTickEvent


@cron('* * * * *')
def tick():
    """store the current timestamp"""
    site = zoom.system.site
    events = zoom.store_of(Event)
    event = events.first(site=site.name) or Event(site=site.name, counter=1)
    event.timestamp = zoom.tools.now()
    event.counter += 1
    event_id = events.put(event)
    return event_id


class TickEventView(zoom.View):

    def index(self):
        site = zoom.system.site
        events = zoom.store_of(Event)
        event = events.first(site=site.name)

        if event:
            msg = 'Tick {event.counter} happened {event.when}'
            message = msg.format(event=event)
        else:
            message = 'No ticks yet.  Background process may not be active.'

        return zoom.page(
            message,
            title='Background'
        )

main = zoom.dispatch(TickEventView)
