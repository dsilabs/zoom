"""
    info

    display system info
"""

import json

from zoom.apps import App
from zoom.page import page
from zoom.helpers import url_for, link_to


class MyApp(App):

    menu = 'Overview', 'Log', 'Missing', 'About'

    def index(self):

        def serializable(i):
            _, v = i
            try:
                json.dumps(v)
                return True
            except TypeError:
                return False

        request = self.request

        links = link_to('hello', '/hello')
        tpl = links + '<pre>{}</pre>'
        request_values = dict(filter(serializable, request.__dict__.items()))
        values = dict(
            request_values,
            data=request.data,
            a_url=url_for('howdy', name='Joe Smith'),
            a_rooted_url=url_for('/howdy', name='Joe Smith'),
        )

        actions = 'New',

        return page(
            tpl.format(json.dumps(values, indent=4)),
            title='System Info',
            actions=actions,
            search=request.data.get('q', ''),
            subtitle='this is the subtitle'
        )

        return page('overview', title='my page')

    def log(self):
        return page('log goes here', title='Log')


app = MyApp()
