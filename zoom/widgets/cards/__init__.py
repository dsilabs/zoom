"""
    cards
"""

import zoom
import zoom.html as html


class Card(zoom.DynamicComponent):

    def format(self, *content, title=None, footer=None): # pylint: disable=arguments-differ
        """Card format

        Format content in the form of a Card.

        """

        header = html.div(title, classed='card-header') if title else ''
        footer = html.div(footer, classed='card-footer') if footer else ''

        card = zoom.Component(
            html.div(
                header,
                html.div(
                    zoom.Component(content).render(),
                    classed='card-body'
                ),
                footer,
                classed='card'
            )
        )

        return zoom.DynamicComponent(
            self,
            card,
        )
