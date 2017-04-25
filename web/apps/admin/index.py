"""
    users index
"""

from zoom.mvc import View
from zoom.page import page
from zoom.users import Users
from zoom.browse import browse
from zoom.tools import load_content
from zoom.component import Component

from users import user_fields
from views import PanelView, index_metrics_view, IndexPageLayoutView


class MyView(View):

    def index(self, q=''):
        db = self.model.site.db

        users = Users(db)
        groups = db('select * from groups')
        members = db('select * from members')
        subgroups = db('select * from subgroups')

        content = Component(
            index_metrics_view(db),
            IndexPageLayoutView(
                feed1=Component(
                    PanelView(title='Users', content=browse(users)),
                    PanelView(title='Groups', content=browse(groups)),
                ),
                feed2=PanelView(title='Memberships', content=browse(members)),
                feed3=PanelView(title='Subgroups', content=browse(subgroups)),
            ),
        )
        return page(content, title='Overview', subtitle='Raw dump of main tables', search=q)

    def about(self, *a):
        return page(load_content('about.md'))


def main(route, request):
    """main program"""
    view = MyView(request)
    return view(*request.route[1:], **request.data)
