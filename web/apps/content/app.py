"""
    content app
"""

from zoom.apps import App
from zoom.page import page
from zoom.tools import load_content, home
import traceback
import logging


class CustomApp(App):

    def __call__(self, request):
        logger = logging.getLogger(__name__)
        logger.debug('called content app with (%r) (%r)', request.route, request.path)

        if request.path == '/':
            # this is a request to view the site index page
            request.path = '/show'
            request.route =  request.path.split('/')
            return App.__call__(self, request)

        elif request.path.endswith('.html'):
            # this is a request to view a site page
            request.path = request.path + '/show'
            request.route =  request.path.split('/')
            return App.__call__(self, request)

        elif request.route and request.route[0] == 'content':
            # this is a request to manage site content
            self.menu = ['Overview', 'Pages', 'Snippets']
            return App.__call__(self, request)


app = CustomApp()
