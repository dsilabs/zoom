"""
    sample responses
"""

import zoom

class View(zoom.View):

    def index(self):
        """Index"""

        return zoom.tools.markdown("""
        # Responses
        * [str](/sample/responses/string)
        * [text](/sample/responses/text)
        * [Component](/sample/responses/component)
        * [Missing (404)](/sample/responses/missing)
        """)

    def string(self):
        return '<h1>Str</h1>This is a <code>str</code> response.'

    def text(self):
        t = 'This is a TextResponse response.'
        return zoom.response.TextResponse(t)

    def component(self):
        return zoom.Component('<h1>Component</h1>This is a <code>Component</code> response.')


main = zoom.dispatch(View)