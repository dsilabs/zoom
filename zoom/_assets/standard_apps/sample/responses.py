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
        * [Missing (404)](/sample/responses/missing)
        """)

    def string(self):
        return '<h1>Str</h1>This is a <code>str</code> response.'

    def text(self):
        return zoom.response.TextResponse('This is a TextResponse response')


main = zoom.dispatch(View)