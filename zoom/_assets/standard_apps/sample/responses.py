"""
    sample responses
"""

import zoom


class Person(zoom.Record):
    """Person Record"""


class View(zoom.View):

    def index(self):
        """Index"""

        return zoom.tools.markdown("""
        # Responses
        * [str](/sample/responses/string)
        * [dict](/sample/responses/dictionary)
        * [Record](/sample/responses/record)
        * [text](/sample/responses/text)
        * [Component](/sample/responses/component)
        * [Missing (404)](/sample/responses/missing)
        """)

    def string(self):
        return '<h1>Str</h1>This is a <code>str</code> response.'

    def dictionary(self):
        return dict(name='Dict Response', content='This is a dict response.')

    def record(self):
        return Person(
            name='Record Response',
            address='1234 Somwhere St',
            content='This is a zoom.Record response.',
        )

    def text(self):
        t = 'This is a TextResponse response.'
        return zoom.response.TextResponse(t)

    def component(self):
        return zoom.Component('<h1>Component</h1>This is a <code>Component</code> response.')


main = zoom.dispatch(View)