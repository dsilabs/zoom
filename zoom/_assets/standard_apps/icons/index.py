"""
    icons index
"""

import zoom

class MyView(zoom.View):
    """Index View"""

    def index(self):
        """Index page"""
        zoom.requires('fontawesome4')
        zoom.requires('bootstrap-icons')

        content = '<h2>Bootstrap Icons 1.7.2</h2>'
        content += '<p>{}</p>'.format(zoom.tools.load('bi-icons.html'))

        content += '<h2>FontAwesome 4</h2>'
        content += '<p>{}</p>'.format(zoom.tools.load('fa-icons.html'))

        return zoom.page(
            content,
            title='Icons',
            subtitle='Hover over icon to see name',
            css=".content .fa, .content .bi { color: #555 }"
        )

    def about(self):
        """About page"""
        content = '{app.description}'
        return zoom.page(
            content.format(app=zoom.system.request.app),
            title='About {app.title}'.format(app=zoom.system.request.app)
        )


main = zoom.dispatch(MyView)
