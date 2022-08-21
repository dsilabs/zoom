"""
    App Index

    Provides the main index for the app.
"""

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

