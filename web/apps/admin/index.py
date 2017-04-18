"""
    users index
"""

from zoom.mvc import View
from zoom.page import page
from zoom.users import Users
from zoom.browse import browse
from zoom.tools import load_content
from zoom.component import component
from users import user_fields

class MyView(View):

    def index(self, q=''):
        db = self.model.site.db
        users = Users(db)
        content = component(
            browse(users, title='Users'),
            browse(db('select * from members'), title='Memberships'),
            browse(db('select * from groups'), title='Groups'),
            browse(db('select * from subgroups'), title='Subgroups')
        )
        return page(content, title='Overview', subtitle='Raw dump of main tables')

    def about(self):
        return page(load_content('about.md'))


def main(route, request):
    """main program"""
    view = MyView(request)
    return view(*request.route[1:], **request.data)
