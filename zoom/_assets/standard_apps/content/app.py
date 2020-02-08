"""
    content app
"""

import logging

import zoom
from zoom.apps import App

menu = ['Overview', 'Pages', 'Snippets', 'Images', 'Files']


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

        images_paths = ['/content/images', '/content/images/edit']
        files_paths = ['/content/files', '/content/files/edit']

        if request.path == '/':
            # this is a request to view the site index page
            request.path = '/show'
            request.route = request.path.split('/')
            return App.__call__(self, request)

        elif request.path == '/content/sitemap':
            return App.__call__(self, request)

        elif request.path in images_paths and zoom.system.user.can('edit', self):
            # user with edit privilege is viewing the image manager index
            self.menu = menu
            return App.__call__(self, request)

        elif request.path in files_paths and zoom.system.user.can('edit', self):
            # user with edit privilege is viewing the file manager index
            self.menu = menu
            return App.__call__(self, request)

        elif request.path.startswith('/content/images') and request.path != '/content/images':
            # any user is viewing an image
            return App.__call__(self, request)

        elif request.path.startswith('/content/files') and request.path != '/content/files':
            # any user is viewing a file
            return App.__call__(self, request)

        elif request.path.endswith('.html'):
            # this is a request to view a site page
            request.path = request.path + '/show'
            request.route = request.path.split('/')
            return App.__call__(self, request)

        elif request.path == '/content/images/get-image':
            # user is viewing an image
            return App.__call__(self, request)

        elif request.route and request.route[0] == 'content' and zoom.system.user.can('edit', self):
            # this is a request to manage site content
            self.menu = menu
            return App.__call__(self, request)

        return None


app = CustomApp()
