"""
    content.index
"""

from datetime import datetime
import logging
import os

from zoom.mvc import View
from zoom.page import page
from zoom.browse import browse

from pages import load_page


class MyView(View):

    def index(self):
        return page('Metrics and activity log and statistics will go here.', title='Overview')

    def show(self, path=None):
        template = 'default'
        if path == None or path == 'content/index.html':
            path = ''
            template = 'index'
        else:
            path = '/'.join(path.split('/')[1:])
        content = load_page(path)
        if content:
            return page(content, template=template)

view = MyView()
