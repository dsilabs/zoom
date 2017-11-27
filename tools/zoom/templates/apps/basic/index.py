"""
    basic index
"""

import zoom

class MyView(zoom.View):
    """Index View"""


    def index(self):
        """Index page"""
        return zoom.page('Content goes here', title='Overview')


    def about(self):
        """About page"""
        content = '{app.description}'
        return zoom.page(
            content.format(app=zoom.system.request.app),
            title='About {app.title}'.format(app=zoom.system.request.app)
        )


view = MyView()
