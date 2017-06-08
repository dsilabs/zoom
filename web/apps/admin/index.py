"""
    users index
"""

from zoom.audit import audit
from zoom.mvc import View
from zoom.page import page
from zoom.users import Users
from zoom.browse import browse
from zoom.logging import log_activity
from zoom.tools import load_content, today
from zoom.component import Component
from zoom.helpers import link_to
from zoom.utils import pretty

# from users import user_fields
from views import PanelView, index_metrics_view, IndexPageLayoutView


class MyView(View):

    def index(self, q=''):
        db = self.model.site.db

        users = sorted(Users(db).find(status='A'), key=lambda a: a.name)
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

    def audit(self):
        db = self.model.site.db
        log_data = db("""
            select *
            from audit_log
            order by timestamp desc
            limit 100""")
        return page(browse(log_data), title='Activity')

    def requests(self):
        db = self.model.site.db
        log_data = db("""
            select *
            from log
            where status in ('C', 'I')
            order by timestamp desc
            limit 100""")
        return page(browse(log_data), title='Requests')

    def activity(self):
        db = self.model.site.db
        log_data = db("""
            select *
            from log
            where status in ('A')
            order by timestamp desc, id desc
            limit 100""")
        return page(browse(log_data), title='Activity')

    def show_error(self, key):
        db = self.model.site.db
        log_entry = db('select * from log where id=%s', key).first()

        content = '<br><br>'.join(map(str, log_entry)).replace(
            '\n', '<br>'
        )
        return page(content, title='Log Entry')

    def errors(self, n=0, limit=50):
        offset = int(n) * int(limit)
        db = self.model.site.db
        log_data = db("""
            select
                id,
                user_id,
                address,
                app,
                path,
                timestamp,
                elapsed
            from log
            where status='E'
            order by timestamp desc
            limit {limit}
            offset {offset}""".format(**locals()))
        labels = 'id', 'user', 'address', 'app', 'path', 'timestamp', 'elapsed'
        data = [
            [link_to(str(item[0]), '/admin/show_error/' + str(item[0]))] + list(item[1:])
            for item in log_data
        ]
        return page(browse(data, labels=labels), title='Errors')

    def configuration(self):
        return page(load_content('configuration.md').format(request=self.model))

    def about(self, *a):
        return page(load_content('about.md'))


def main(route, request):
    """main program"""
    view = MyView(request)
    return view(*request.route[1:], **request.data)
