"""
    zoom.page
"""

import logging

from zoom.component import composition, Component
from zoom.components import as_actions
from zoom.response import HTMLResponse
from zoom.mvc import DynamicView

import zoom.html as html
import zoom.apps
import zoom.forms
import zoom.helpers
import zoom.render

class ClearSearch(DynamicView):
    pass


class SearchBox(DynamicView):

    request_path = '<dz:request_path>'

    @property
    def clear(self):
        if self.value:
            return ''.join(ClearSearch().render().parts['html'])
        else:
            return ''


class PageHeader(DynamicView):
    """page header"""

    @property
    def title(self):
        return self.page.title

    @property
    def subtitle(self):
        return self.page.subtitle

    @property
    def action_items(self):
        return as_actions(self.page.actions)

    @property
    def search_box(self):
        if self.page.search is None:
            return ''
        else:
            search_box = SearchBox(value=self.page.search)
            return ''.join(search_box.render().parts['html'])


class Page(object):
    """a web page"""

    def __init__(self, content, *args, **kwargs):
        self.content = content
        self.theme = 'default'
        self.template = 'default'
        self.title = ''
        self.subtitle = ''
        self.keywords = ''
        self.description = ''
        self.actions = []
        self.search = None
        self.__dict__.update(kwargs)
        self.args = args
        self.kwargs = kwargs

    def helpers(self, request):
        """provide page helpers"""

        def get_alerts(request):

            pop = request.session.__dict__.pop

            def show(alerts, Class):
                if alerts:
                    return html.div(html.ul(alerts), Class='alert %s' % Class)
                return ''

            success_alerts = pop('system_successes', [])
            successes = show(success_alerts, 'success')

            warning_alerts = pop('system_warnings', [])
            warnings = show(warning_alerts, 'warning')

            error_alerts = pop('system_errors', [])
            errors = show(error_alerts, 'danger')

            return errors + warnings + successes

        def get(part, wrapper='{}'):
            parts = composition.parts.parts.get(part, [])
            logger = logging.getLogger(__name__)
            logger.debug('get_{}: {}'.format(part, parts))
            return parts and '\n'.join(wrapper.format(part) for part in parts) or ''

        def get_css():
            wrapper = '<style>\n{}\n</style>'
            return get('css', wrapper) or '<!-- css missing -->'

        def get_js():
            parts = composition.parts.parts.get('js', [])
            code = '\n'.join(parts)
            if code:
                result = """
                <script>
                $(function(){{
                    {}
                }});
                </script>
                """.format(code)
                return result
            return ''

        def get_libs():
            wrapper = '<script src="{}"></script>'
            return get('libs', wrapper)

        def get_styles():
            wrapper = '<link rel="stylesheet" href="{}">'
            return get('styles', wrapper)

        def get_head():
            return get('head')

        def get_tail():
            return get('tail')

        return dict(
            {'page_' + k: v for k, v in self.__dict__.items()},
            page_title=request.site.title,
            site_url=request.site.url,
            author=request.site.owner_name,
            css=get_css,
            js=get_js(),
            head=get_head(),
            tail=get_tail(),
            styles=get_styles(),
            libs=get_libs(),
            alerts=get_alerts(request),
            stdout='{*stdout*}',
        )

    def render(self, request):
        """render page"""

        def rendered(obj):
            """call the render method if necessary"""
            if hasattr(obj, 'render'):
                return obj.render()
            return obj

        template = request.site.get_template(self.template)

        providers = [
            zoom.helpers.__dict__,
            request.helpers(),
            request.site.helpers(),
            request.user.helpers(),
            zoom.forms.helpers(request),
            zoom.apps.helpers(request),
            self.helpers(request),
        ]

        logger = logging.getLogger(__name__)
        logger.debug('rendering page')

        save_content = self.content

        if self.title or self.subtitle or self.actions or self.search:
            full_page = Component(PageHeader(page=self), self.content)
        else:
            full_page = Component(self.content)

        self.content = full_page.render()
        content = zoom.render.apply_helpers(template, self, providers)
        self.content = save_content

        return HTMLResponse(content)


page = Page  # pylint: disable=invalid-name
