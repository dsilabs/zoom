"""
    content.index
"""

import logging
import os

from zoom.mvc import View
from zoom.page import page
from zoom.browse import browse
from zoom.tools import load_content, home

from datetime import datetime


def load(name):
    if os.path.exists(name + '.md'):
        return load_content(name + '.md')
    logger = logging.getLogger(__name__)
    logger.debug('file not found %r', name + '.md')

class MyView(View):

    def index(self):
        return page('Metrics and activity log and statistics will go here.', title='Overview')

    def show(self, key=None):
        template = 'default'
        if key == None:
            key = 'index'
            template = 'index'
        content = load(key)
        if content:
            return page(content, template=template)

view = MyView()
