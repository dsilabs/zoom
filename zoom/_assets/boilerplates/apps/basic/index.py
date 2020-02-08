"""This file is the index view for our app. It's set up to serve a few pages by
default."""

import zoom

class IndexView(zoom.View):
    """This Zoom "view" serves both an index and about page."""

    def index(self):
        """Index page."""
        return zoom.page('My Zoom app!', title='Overview')

    def about(self):
        """About page."""
        content = '{app.description}'
        return zoom.page(
            content.format(app=zoom.system.request.app),
            title='About {app.title}'.format(app=zoom.system.request.app)
        )

main = zoom.dispatch(IndexView)
