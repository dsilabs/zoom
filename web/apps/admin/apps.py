"""
    administer apps
"""

import zoom

class AppsController(zoom.Controller):

    def index(self):

        def fmt(app):
            name = app.name
            group_name = 'a_' + app.name
            has_group = zoom.system.site.groups.find(name=group_name)
            return [app.name,  app.title, app.path, 'yes' if has_group else 'no']

        data = [fmt(app) for app in sorted(zoom.system.site.apps, key=lambda a: a.name)]
        content = zoom.browse(
            data,
            labels=['App', 'Title', 'Path', 'Group']
        )
        return zoom.page(content, title='Apps')

main = zoom.dispatch(AppsController)