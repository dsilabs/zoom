"""
    users index
"""

import datetime
import json
import os
import sys
import platform

import zoom
import zoom.html as h
from zoom.helpers import link_to, link_to_page
from zoom.page import page
from zoom.tools import load_content, today, how_long_ago
from zoom.users import link_to_user

import views
import users
import groups

def log_data(db, status, n, limit, q):
    """retreive log data"""

    host = zoom.system.request.host

    statuses = tuple(status)
    offset = int(n) * int(limit)
    cmd = """
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
        where status in %s and server = %s
        order by id desc
        limit {limit}
        offset {offset}
        """.format(
            limit=int(limit),
            offset=offset,
            statuses=statuses
        )
    data = db(cmd, statuses, host)
    data = [
        [
            link_to(
                str(item[0]),
                '/admin/entry/' + str(item[0])
            ),
            item[1],
            zoom.helpers.who(item[2]),
        ] + list(item[3:])
        for item in data
        if q in repr(item)
    ]
    labels = (
        'id', 'status', 'user', 'address', 'app',
        'path', 'timestamp', 'elapsed'
    )
    return zoom.browse(data, labels=labels)


def activity_panel(db):

    host = zoom.system.request.host

    data = db("""
    select
        log.id,
        users.username,
        log.address,
        log.path,
        log.timestamp,
        log.elapsed
    from log left join users on log.user_id = users.id
    where server = %s and path not like "%%\\/\\_%%"
    and log.status = 'C'
    order by timestamp desc
    limit 15
    """, host)

    rows = []
    for rec in data:
        row = [
            link_to(str(rec[0]), '/admin/entry/' + str(rec[0])),
            link_to_user(rec[1]),
            rec[2],
            rec[3],
            how_long_ago(rec[4]),
            rec[4],
            rec[5],
        ]
        rows.append(row)

    labels = 'id', 'user', 'address', 'path', 'when', 'timestamp', 'elapsed'
    return zoom.browse(rows, labels=labels, title=link_to_page('Requests'))


def error_panel(db):

    host = zoom.system.request.host

    data = db("""
        select
            log.id,
            username,
            path,
            timestamp
        from log left join users on log.user_id = users.id
        where log.status in ("E") and timestamp>=%s
        and server = %s
        order by log.id desc
        limit 10
        """, today(), host)

    rows = []
    for rec in data:
        row = [
            link_to(str(rec[0]), '/admin/entry/' + str(rec[0])),
            link_to_user(rec[1]),
            rec[2],
            how_long_ago(rec[3]),
        ]
        rows.append(row)

    labels = 'id', 'user', 'path', 'when'
    return zoom.browse(rows, labels=labels, title=link_to_page('Errors'))


def warning_panel(db):

    host = zoom.system.request.host

    data = db("""
        select
            log.id,
            username,
            path,
            timestamp
        from log inner join users on log.user_id = users.id
        where log.status in ("W") and timestamp>=%s
        and server = %s
        order by log.id desc
        limit 10
        """, today(), host)

    rows = []
    for rec in data:
        row = [
            link_to(str(rec[0]), '/admin/entry/' + str(rec[0])),
            link_to_user(rec[1]),
            rec[2],
            how_long_ago(rec[3]),
        ]
        rows.append(row)

    labels = 'id', 'user', 'path', 'when'
    return zoom.browse(rows, labels=labels, title=link_to_page('Warnings'))


def users_panel(db):

    host = zoom.system.request.host

    data = db("""
    select
        users.username,
        max(log.timestamp) as timestamp,
        count(*) as requests
    from log, users
        where log.user_id = users.id
        and timestamp >= %s
        and server = %s
        and path not like "%%\\/\\_%%"
    group by users.username
    order by timestamp desc
    limit 10
    """, today() - datetime.timedelta(days=14), host)

    rows = []
    for rec in data:
        row = [
            link_to_user(rec[0]),
            how_long_ago(rec[1]),
            rec[2],
        ]
        rows.append(row)

    labels = 'user', 'last seen', 'requests'
    return zoom.browse(rows, labels=labels, title=link_to_page('Users'))


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
    return zoom.Component(content, js=js)


class MyView(zoom.View):

    def index(self, q=''):

        content = callback(self._index)

        if q:
            request = zoom.system.request
            users_collection = users.get_users_collection(request)
            user_records = users_collection.search(q)

            groups_collection = groups.get_groups_collection(request)
            group_records = groups_collection.search(q)

            if user_records or group_records:
                content = zoom.Component()
                if group_records:
                    footer = '%d groups found' % len(group_records)
                    content += zoom.browse(
                        group_records,
                        columns=groups_collection.columns,
                        labels=groups_collection.labels,
                        title='Groups',
                        footer=footer,
                    )

                if user_records:
                    footer = '%d users found' % len(user_records)
                    content += zoom.browse(
                        user_records,
                        columns=users_collection.columns,
                        labels=users_collection.labels,
                        title='Users',
                        footer=footer,
                    )
            else:
                zoom.alerts.warning('no records found')

        return page(
            content,
            title='Overview',
            search=q
        )

    def _index(self):
        # return None
        self.model.site.logging = False
        db = self.model.site.db

        content = zoom.Component(
            views.index_metrics_view(db),
            views.IndexPageLayoutView(
                feed1=activity_panel(db),
                feed2=users_panel(db),
                feed3=error_panel(db),
                feed4=warning_panel(db),
            ),
        )
        return content

    def clear(self):
        """Clear the search"""
        return zoom.home()

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
            order by id desc limit 50
            """
        )
        return zoom.browse(data)

    def audit(self):
        """view audit log"""
        def fmt(rec):
            user = (zoom.helpers.who(rec[2]),)
            when = (zoom.helpers.when(rec[-1]),)
            return rec[0:2] + user + rec[3:-1] + when

        db = self.model.site.db
        data = list(map(fmt, db("""
            select
                *
            from audit_log
            order by id desc
            limit 100"""
        )))

        labels = 'ID', 'App', 'By Whom', 'Activity', 'Subject 1', 'Subject 2', 'When'
        return page(zoom.browse(data, labels=labels), title='Activity')

    def requests(self, show_all=False):
        def fmt(rec):
            entry = (link_to(str(rec[0]), '/admin/entry/' + str(rec[0])),)
            user = (zoom.helpers.who(rec[4]),)
            return entry + rec[1:4] + user + rec[5:]
        path_filter = '' if show_all else 'and path not like "%%\\/\\_%%"'
        db = self.model.site.db
        data = db("""
            select
                id, app, path, status, user_id, address, login, timestamp, elapsed
            from log
            where status in ('C', 'I', 'W')
            and server = %s
            {}
            order by id desc
            limit 100""".format(path_filter), zoom.system.request.host)
        labels = 'id', 'app', 'path', 'status', 'user', 'address', 'login', 'timestamp', 'elapsed'
        data = list(map(fmt, data))
        actions = () if show_all else ('Show All',)
        return page(zoom.browse(data, labels=labels), title='Requests', actions=actions)

    def performance(self, n=0, limit=50, q=''):
        db = self.model.site.db
        return page(log_data(db, ['P'], n, limit, q), title='Performance', search=q, clear='/admin/performance')

    def activity(self, n=0, limit=50, q=''):
        db = self.model.site.db
        return page(log_data(db, ['A'], n, limit, q), title='Activity', search=q, clear='/admin/activity')

    def errors(self, n=0, limit=50, q=''):
        db = self.model.site.db
        return page(log_data(db, ['E'], n, limit, q), title='Errors', search=q, clear='/admin/errors')

    def warnings(self, n=0, limit=50, q=''):
        db = self.model.site.db
        return page(log_data(db, ['W'], n, limit, q), title='Warnings', search=q, clear='/admin/warnings')

    def entry(self, key):

        def fmt(item):
            name, value = item
            return name, zoom.html.pre(value)

        entries = zoom.table_of('log')
        entry = list(entries.first(id=key).items())

        visible = lambda a: not a[0].startswith('_')

        content = zoom.html.table(
            map(fmt, filter(visible, entry))
        )
        css = """
        .content table {
            width: 80%;
            vertical-align: top;
        }
        .content table td:nth-child(1) {
            width: 30%;
        }
        .content table td {
            padding: 5px;
            line-height: 20px;
        }
        .content table pre {
            padding: 0px;
            background: 0;
            border: none;
            line-height: 20px;
            margin: 0;
        }
        """
        return page(content, title='Log Entry', css=css)

    def configuration(self):
        if zoom.system.request.site.profiling:
            if zoom.system.request.profiling:
                profiling_message = 'Yes'
            else:
                profiling_message = 'No <span class="hint">(environment variable missing)</span>'
        else:
            profiling_message = 'No'

        items = zoom.packages.get_registered_packages()
        packages = '\n'.join(
            '<dt>{}</dt><dd>{}</dd>'.format(
                key,
                '<br>'.join(
                    '{resources}'.format(
                        resources='<br>'.join(resources)
                    ) for resource_type, resources
                    in sorted(parts.items(), key=lambda a: ['requires', 'styles', 'libs'].index(a[0]))
                )
            )
            for key, parts in sorted(items.items())
        )

        apps_paths = '<br>'.join(zoom.system.request.site.apps_paths)

        return page(
            load_content(
                'configuration.md',
                request=zoom.system.request,
                packages=packages,
                profiling=profiling_message,
                apps_paths=apps_paths,
            ),
        )

    def environment(self):
        return page(
            zoom.Component(
                h.h2('Zoom'),
                zoom.html.table([
                    ('Version', zoom.__version__ + ' Community Edition'),
                ]),
                h.h2('Python'),
                zoom.html.table([
                    ('sys.version', sys.version),
                    ('sys.path', '<br>'.join(sys.path)),
                ]),
                h.h2('Operating System'),
                zoom.html.table([
                    ('Name', os.name),
                    ('PATH', '<br>'.join(os.environ.get('PATH').split(':')))
                ]),
                h.h2('Platform'),
                zoom.html.table([
                    ('Node', platform.node()),
                    ('System', platform.system()),
                    ('Machine', platform.machine()),
                    ('Archtitecture', ' '.join(platform.architecture()))
                ]),
                h.h2('Variables'),
                zoom.html.table(
                    list(os.environ.items())
                ),
                css = """
                    .content table { width: 100%; }
                    .content table td { vertical-align: top; width: 70%; }
                    .content table td:first-child { width: 25%; }
                """
            ),
            title='Environment'
        )

    def about(self, *a):
        return page(load_content('about.md'))


def main(route, request):
    """main program"""
    view = MyView(request)
    return view(*request.route[1:], **request.data)
