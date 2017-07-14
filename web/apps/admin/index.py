"""
    users index
"""

# from zoom.audit import audit
from zoom.component import component
from zoom.context import context
from zoom.mvc import View
from zoom.page import page
from zoom.browse import browse
from zoom.tools import load_content, today, how_long_ago
from zoom.component import Component
from zoom.helpers import link_to

from views import index_metrics_view, IndexPageLayoutView


def log_data(db, status, n, limit, q):
    """retreive log data"""
    statuses = ','.join("'{}'".format(s) for s in status)
    offset = int(n) * int(limit)
    data = db("""
        select
            id,
            status,
            user_id,
            address,
            app,
            path,
            timestamp,
            elapsed
        from log
        where status in ({statuses})
        order by timestamp desc
        limit {limit}
        offset {offset}
        """.format(
            limit=limit,
            offset=offset,
            statuses=statuses
        )
    )
    data = [
        [
            link_to(
                str(item[0]),
                '/admin/show_error/' + str(item[0])
            )
        ] + list(item[1:])
        for item in data
        if q in repr(item)
    ]
    labels = (
        'id', 'status', 'user', 'address', 'app',
        'path', 'timestamp', 'elapsed'
    )
    return browse(data, labels=labels)


def activity_panel(db):
    data = db("""
    select
        log.id,
        users.username,
        log.address,
        log.path,
        log.timestamp,
        log.elapsed
    from log, users
        where log.user_id = users.id
    order by timestamp desc
    limit 15
    """)

    rows = []
    for rec in data:
        row = [
            link_to(str(rec[0]), '/admin/show_error/' + str(rec[0])),
            link_to(rec[1], '/admin/users/' + rec[1]),
            rec[2],
            rec[3],
            how_long_ago(rec[4]),
            rec[4],
            rec[5],
        ]
        rows.append(row)

    labels = 'id', 'user', 'path', 'address', 'when', 'timestamp', 'elapsed'
    return browse(rows, labels=labels, title='Activity')


def error_panel(db):
    data = db("""
        select
            id,
            user_id,
            path,
            timestamp
        from log
        where status in ("E") and timestamp>={today}
        order by timestamp desc
        limit 10
        """.format(today=today()))

    users = context.site.users
    rows = []
    for rec in data:
        row = [
            link_to(str(rec[0]), '/admin/show_error/' + str(rec[0])),
            users.get(rec[1]).link,
            rec[2],
            how_long_ago(rec[3]),
        ]
        rows.append(row)

    labels = 'id', 'user', 'path', 'when'
    return browse(rows, labels=labels, title='Errors')


def users_panel(db):
    data = db("""
    select
        users.username,
        max(log.timestamp) as timestamp,
        count(*) as requests
    from log, users
        where log.user_id = users.id and users.status="A"
    group by users.username
    order by timestamp desc
    limit 10
    """)

    rows = []
    for rec in data:
        row = [
            link_to(rec[0], '/admin/users/' + rec[0]),
            how_long_ago(rec[1]),
            rec[2],
        ]
        rows.append(row)

    labels = 'user', 'last seen', 'requests'
    return browse(rows, labels=labels, title='User Activity')


def callback(method, url=None, timeout=5000):
    method_name = method.__name__
    path = url or '/<dz:app_name>/' + method_name
    js = """
        jQuery(function($){
          setInterval(function(){
            $.get('%(path)s', function( content ){
              if (content) {
                    $('#%(method_name)s').html( content );
                }
            });
          }, %(timeout)s);
        });
    """ % dict(
        path=path,
        method_name=method_name,
        timeout=timeout
    )
    content = '<div id="%(method_name)s">%(initial_value)s</div>' % dict(
        initial_value=method(),
        method_name=method_name
    )
    return component(content, js=js)


class MyView(View):

    def index(self, q=''):
        # return page(self._index(), title='Overview')
        return page(callback(self._index), title='Overview')

    def _index(self):
        # return None
        self.model.site.logging = False
        db = self.model.site.db

        content = Component(
            index_metrics_view(db),
            IndexPageLayoutView(
                feed1=activity_panel(db),
                feed2=users_panel(db),
                feed3=error_panel(db),
            ),
        )
        return content

    def log(self):
        """view system log"""
        save_logging = self.model.site.logging
        try:
            content = callback(self._system_log)
        finally:
            self.model.site.logging = save_logging
        return page(content, title='System Log')

    def _system_log(self):
        self.model.site.logging = False
        db = self.model.site.db
        data = db(
            """
            select
                id, app, path, status, address, elapsed, message
            from log
            order by timestamp desc limit 50
            """
        )
        return browse(data)

    def audit(self):
        """view audit log"""
        db = self.model.site.db
        data = db("""
            select *
            from audit_log
            order by timestamp desc
            limit 100""")
        return page(browse(data), title='Activity')

    def requests(self):
        db = self.model.site.db
        data = db("""
            select *
            from log
            where status in ('C', 'I')
            order by timestamp desc
            limit 100""")
        return page(browse(data), title='Requests')

    def performance(self, n=0, limit=50, q=''):
        db = self.model.site.db
        return page(log_data(db, ['P'], n, limit, q), title='Performance', search=q, clear='/admin/performance')

    def activity(self, n=0, limit=50, q=''):
        db = self.model.site.db
        return page(log_data(db, ['A'], n, limit, q), title='Activity', search=q, clear='/admin/activity')

    def errors(self, n=0, limit=50, q=''):
        db = self.model.site.db
        return page(log_data(db, ['E'], n, limit, q), title='Errors', search=q, clear='/admin/errors')

    def show_error(self, key):
        db = self.model.site.db
        log_entry = db('select * from log where id=%s', key).first()

        content = '<br><br>'.join(map(str, log_entry)).replace(
            '\n', '<br>'
        )
        return page(content, title='Log Entry')

    def configuration(self):
        return page(load_content('configuration.md').format(request=self.model))

    def about(self, *a):
        return page(load_content('about.md'))


def main(route, request):
    """main program"""
    view = MyView(request)
    return view(*request.route[1:], **request.data)
