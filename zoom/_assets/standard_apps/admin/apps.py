"""
    administer apps
"""

import logging
import zoom

logger = logging.getLogger(__name__)


class AppsController(zoom.Controller):

    def index(self):

        def get_group_link(group_id):
            """Return a group link"""
            group = groups.get(group_id)
            return group.link if group else zoom.html.span(
                'missing',
                title='unknown subgroup id {!r}'.format(group_id)
            )

        def get_type(app):
            try:
                return zoom.tools.websafe(app.method.__class__.__name__)
            except BaseException as e:
                logging.error('Error examinging app: %s', e)
                return 'Unknown'

        def fmt(app):
            """Format an app record"""
            name = app.name
            group_name = 'a_' + app.name
            app_group = zoom.system.site.groups.first(name=group_name)
            groups = ', '.join(
                get_group_link(s) for g, s in subgroups if g == app_group._id
            ) or 'none' if app_group else ''
            return [
                app.title,
                app.name,
                get_type(app),
                app.path,
                groups,
                (bool(app.in_development) and 'development' or '')
            ]

        db = zoom.system.site.db
        subgroups = list(db('select * from subgroups'))
        groups = dict((g.group_id, g) for g in zoom.system.site.groups)
        data = [fmt(app) for app in sorted(zoom.system.site.apps, key=lambda a: a.title.lower())]
        content = zoom.browse(
            data,
            labels=['Title', 'App', 'Type', 'Path', 'Groups', 'Status']
        )
        return zoom.page(content, title='Apps')

main = zoom.dispatch(AppsController)

