"""
    settings.index
"""

import zoom
import zoom.html as h

import model


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


class SettingsView(zoom.mvc.View):
    """Settings View"""

    def about(self):
        return zoom.page(zoom.tools.load_content('about.md'))


class SettingsController(zoom.mvc.Controller):
    """Settings Controller"""

    menu = SettingsManager(
        'Site',
        'Theme',
        'Mail',
        title='System Settings'
    )

    site_form = model.get_site_settings_form()
    theme_form = model.get_theme_settings_form()
    mail_form = model.get_mail_settings_form()

    def index(self, selected=None, *args, **kwargs):
        """index page"""
        return zoom.home('site')

    def reset(self):
        zoom.system.site.settings.clear()
        return zoom.home('mail')

    def site(self, *args, **kwargs):
        return zoom.page(self.site_form.edit(), title='Site')

    def theme(self, *args, **kwargs):
        return zoom.page(self.theme_form.edit(), title='Theme')

    def mail(self, *args, **kwargs):
        return zoom.page(self.mail_form.edit(), title='Mail')

    def save_button(self, *args, **kwargs):

        if args and args[0] == 'site':
            if self.site_form.validate(kwargs):
                model.save_site_settings(self.site_form.evaluate())
                zoom.alerts.success('site settings saved')
                return zoom.home(args[0])
            return None

        if args and args[0] == 'theme':
            if self.theme_form.validate(kwargs):
                model.save_theme_settings(self.theme_form.evaluate())
                zoom.alerts.success('theme settings saved')
                return zoom.home(args[0])
            return None

        if args and args[0] == 'mail':
            if self.mail_form.validate(kwargs):
                model.save_mail_settings(self.mail_form.evaluate())
                zoom.alerts.success('mail settings saved')
                return zoom.home(args[0])
            return None


    def __call__(self, *args, **kwargs):
        response = zoom.mvc.Controller.__call__(self, *args, **kwargs)
        return self.menu.page(response)


main = zoom.dispatch(SettingsController, SettingsView)
