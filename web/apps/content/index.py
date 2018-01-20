"""
    content.index
"""

import zoom
from zoom.mvc import View

from pages import load_page


class MyView(View):
    """View"""

    @staticmethod
    def index():
        """app index"""
        return zoom.page(
            'Metrics and activity log and statistics will go here.',
            title='Overview'
        )

    def show(self, *args, **kwargs):
        """Show a page"""
        path = '/'.join(args) if args else None
        template = 'default'

        if path is None or path == 'content/index.html':
            path = ''
            template = 'index'
        else:
            path = '/'.join(path.split('/')[1:])

        content = load_page(path)
        if content:
            return zoom.page(content, template=template)
        return None

view = MyView()
