"""
    administer apps
"""

import zoom

class AppsController(zoom.Controller):

    def index(self):

        def get_group_link(group_id):
            group = groups.get(group_id)
            return group.link if group else zoom.html.span(
                'missing',
                title='unknown subgroup id {!r}'.format(group_id)
            )

        def fmt(app):
            name = app.name
            group_name = 'a_' + app.name
            app_group = zoom.system.site.groups.first(name=group_name)
            groups = ', '.join(
                get_group_link(s) for g, s in subgroups if g == app_group._id
            ) if app_group else ''
            return [
                app.title,
                app.name,
                app.path,
                groups,
            ]

        db = zoom.system.site.db
        subgroups = list(db('select * from subgroups'))
        groups = dict((g._id, g) for g in zoom.system.site.groups)
        data = [fmt(app) for app in sorted(zoom.system.site.apps, key=lambda a: a.title.lower())]
        content = zoom.browse(
            data,
            labels=['Title', 'App', 'Path', 'Groups']
        )
        return zoom.page(content, title='Apps')

main = zoom.dispatch(AppsController)

