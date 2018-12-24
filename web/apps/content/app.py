"""
    content app
"""

import logging

import zoom
from zoom.apps import App


class CustomApp(App):
    """Content App"""
    # pylint: disable=R0903

    def allows(self, user, action):
        return user.is_member('managers')

    def __call__(self, request):
        logger = logging.getLogger(__name__)
        logger.debug(
            'called content app with (%r) (%r)', request.route, request.path
        )

        if request.path == '/':
            # this is a request to view the site index page
            request.path = '/show'
            request.route = request.path.split('/')
            return App.__call__(self, request)

        elif request.path.endswith('.html'):
            # this is a request to view a site page
            request.path = request.path + '/show'
            request.route = request.path.split('/')
            return App.__call__(self, request)

        elif request.route and request.route[0] == 'content' and zoom.system.user.can('edit', self):
            # this is a request to manage site content
            self.menu = ['Overview', 'Pages', 'Snippets']
            return App.__call__(self, request)

        return None


app = CustomApp()
