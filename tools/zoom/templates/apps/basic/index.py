"""
    basic index
"""

from zoom.mvc import View, Controller
from zoom.page import page
from zoom.context import context

class MyView(View):

    def index(self):
        return page('Content goes here', title='Overview')


    def about(self):
        content = '{app.description}'
        return page(
            content.format(app=context.request.app),
            title='About {app.title}'.format(app=context.request.app)
        )

view = MyView()
