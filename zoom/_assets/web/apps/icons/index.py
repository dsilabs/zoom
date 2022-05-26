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

        layout = zoom.component.load_component('layout')

        return zoom.page(
            layout.format(
                zoom.tools.load('bi-icons.html'),
                zoom.tools.load('fa-icons.html')
            ),
            title='Icons'
        )

    def about(self):
        """About page"""
        content = '{app.description}'
        return zoom.page(
            content.format(app=zoom.system.request.app),
            title='About {app.title}'.format(app=zoom.system.request.app)
        )


main = zoom.dispatch(MyView)
