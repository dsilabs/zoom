"""
    content.index
"""

from zoom.mvc import View
from zoom.page import page
from zoom.browse import browse

from datetime import datetime


class MyView(View):

    def index(self):
        fake_pages = [
            dict(name='index', content='this is the home page', created=datetime(2017,1,1), created_by='herb'),
            dict(name='page-one', content='this is page one', created=datetime(2017,1,1), created_by='herb'),
        ]
        return page(browse(fake_pages), title='Pages')

    def show(self, *keys):
        content = 'page: {!r}'.format(keys)
        return page(content, title='Show Page')


view = MyView()
