"""
    icons index
"""

import zoom

class MyView(zoom.View):
    """Index View"""

    def index(self):
        """Index page"""
        zoom.requires('fontawesome4')
        content = zoom.tools.load('icons.html')
        subtitle = 'Icons available as part of FontAwesome 4<br><br>'
        return zoom.page(content, title='Icons', subtitle=subtitle)

    def about(self):
        """About page"""
        content = '{app.description}'
        return zoom.page(
            content.format(app=zoom.system.request.app),
            title='About {app.title}'.format(app=zoom.system.request.app)
        )


main = zoom.dispatch(MyView)
