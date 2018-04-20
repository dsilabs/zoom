"""
    settings.index
"""

import zoom
import zoom.html as h


def side_menu(*items):
    css = """
    .side-nav ul li {
        height: 2em;
        line-height: 2em;
        padding: 0 0.5em;
        list-style-type: none;
    }
    .side-nav ul .active {
        background: #ddd;
    }
    .content ul {
        margin-left: 0;
    }
    """
    result = []
    for item in items:
        item_id = zoom.utils.id_for(item)
        route = zoom.system.request.route
        attr = route[1:][:1] == [item_id] and {'class': 'active'} or {}
        result.append(
            h.tag('li',
                h.tag(
                    'a',
                    item,
                    href=zoom.helpers.url_for_page(item_id),
                    id=item_id
                ),
                **attr
            )
        )
    return zoom.Component(
        h.tag('ul', ''.join(result), classed='side-nav'),
        css=css,
    ) if result else ''


class SettingsManager(object):
    def __init__(self, *items, **kwargs):
        self.items = items
        self.common_kwargs = kwargs

    def page(self, response, *args, **kwargs):

        if not isinstance(response, zoom.page):
            return response

        menu = side_menu(*self.items)

        search = getattr(response, 'search', None)
        actions = getattr(response, 'actions', [])
        content = response.content

        layout = h.div(
            h.div(menu, Class='col-md-3 side-nav') +
            h.div(content, Class='col-md-9'),
            classed='row'
        )

        page_args = self.common_kwargs.copy()
        page_args.update(kwargs)

        return zoom.page(
            layout,
            search=search,
            actions=actions,
            *args,
            **page_args
        )


class SettingsView(zoom.mvc.Dispatcher):
    """Setttings View
    """

    menu = SettingsManager(
        'General',
        'Theme',
        # 'Blacklist Addresses',
        'Mail',
        title='System Settings'
    )

    def index(self, selected=None, *a, **kwarg):
        """index page"""
        return zoom.home('general')
        # return zoom.page('dashboard could go here')

    def general(self, *args, **kwargs):
        return zoom.page('<h2>General</h2>General site settings will go here.')

    def theme(self, *args, **kwargs):
        return zoom.page('<h2>Theme</h2>theme settings to go here')

    # def blacklist_addresses(self, *args, **kwargs):
    #     def blacklist_addresses():
    #         return zoom.fields.Fields(
    #             zoom.fields.TextField('IP Address', zoom.validators.required),
    #         )
    #     return zoom.collect.Collection(blacklist_addresses).process(*args, **kwargs)

    def mail(self, *args, **kwargs):
        return zoom.page('<h2>Mail</h2>mail settings to go here')

    def __call__(self, *args, **kwargs):
        response = zoom.mvc.Dispatcher.__call__(self, *args, **kwargs)
        return self.menu.page(response)

main = zoom.dispatch(SettingsView)
