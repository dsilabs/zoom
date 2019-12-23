from datetime import datetime

import zoom
from zoom.context import context
from zoom.store import Entity, store_of
from zoom.background import cron
from zoom.mvc import View

class SampleAppTickEvent(Entity):

    @classmethod
    def store(cls):
        return store_of(cls)

    @classmethod
    def get_all(cls):
        return cls.store().find(site=context.site.name)

    @classmethod
    def get_last(cls):
        all_events = cls.get_all()
        last = None
        for event in all_events:
            if not last or event.count > last.count:
                last = event
        return last

@cron('* * * * *')
def tick():
    existing = SampleAppTickEvent.get_last()
    count = existing.count + 1 if existing else 0
    return SampleAppTickEvent.store().put(SampleAppTickEvent(
        time=datetime.now().isoformat(),
        count=count,
        site=context.site.name
    ))

class TickEventView(View):

    def index(self):
        last = SampleAppTickEvent.get_last()
        return zoom.page('<h1>Background ticks</h1><p>' + ('''
            Last tick (#%d) was at %s.
        '''%(last.count, last.time) if last else '''
            No ticks yet. Background jobs probably aren't set up to run.
        ''') + '</p>')

view = TickEventView()
