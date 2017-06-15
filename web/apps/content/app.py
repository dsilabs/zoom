"""
    content app
"""

from zoom.apps import App
from zoom.page import page
from zoom.tools import load_content
import traceback

class CustomApp(App):

    def __call__(self, request):
        if request.route and request.route[0] == 'content':
            self.menu = ['Overview', 'Pages']
            return App.__call__(self, request)

        else:
            content = load_content('content.md')
            return page(content)

app = CustomApp()
