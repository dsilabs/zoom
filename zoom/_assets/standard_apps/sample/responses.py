"""
    sample responses
"""

import zoom

class View(zoom.View):

    def index(self):
        """Index"""

        return zoom.tools.markdown("""
        # Responses
        * [Missing (404)](/sample/responses/missing)
        """)


main = zoom.dispatch(View)