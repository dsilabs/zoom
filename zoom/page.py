"""
    zoom.page
"""

import io
import logging
import sys

from zoom.component import composition, Component
from zoom.components import as_actions
from zoom.response import HTMLResponse
from zoom.mvc import DynamicView
from zoom.utils import OrderedSet

import zoom.html as html
import zoom.apps
import zoom.forms
import zoom.helpers
import zoom.render
import zoom.tools

class ClearSearch(DynamicView):
    pass

    # @property
    # def clear_url(self):
    #     return '/clearurl'


class SearchBox(DynamicView):

    request_path = '<dz:request_path>'
    clear_url = '<dz:request_path>/clear'

    @property
    def clear(self):
        if self.value:
            return ''.join(ClearSearch(clear_url=self.clear_url).render().parts['html'])
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
            if self.page.clear is None:
                search_box = SearchBox(value=self.page.search)
            else:
                search_box = SearchBox(value=self.page.search, clear_url=self.page.clear)
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
        self.clear = None
        self.__dict__.update(kwargs)
        self.args = args
        self.kwargs = kwargs

    def helpers(self, request):
        """provide page helpers"""

        def get_alerts(request):
            """get alert messages as unordered lists"""

            def get_alert(name, Class):
                """get an alert as an unordered list"""
                alerts = list(composition.parts.parts.pop(name, []))
                if alerts:
                    return html.div(html.ul(alerts), Class='alert %s' % Class)
                return ''

            successes = get_alert('success', 'success')
            warnings = get_alert('warning', 'warning')
            errors = get_alert('error', 'danger')

            return errors + warnings + successes

        def get(part, formatter='{}', joiner='\n'):
            parts = composition.parts.parts.get(part, OrderedSet())
            page_part = getattr(self, part, '')
            if page_part:
                if isinstance(page_part, (list, tuple)):
                    parts |= page_part
                else:
                    parts |= [page_part]
            return parts and joiner.join(
                formatter.format(part) for part in parts
            ) + '\n' or ''

        def get_css():
            wrapper = '<style>\n{}\n</style>'
            content = get('css')
            return content and wrapper.format(content) or ''

        def get_js():
            wrapper = """
                <script>
                $(function(){{
                    {}
                }});
                </script>
                """
            joiner = ';\n    '
            content = get('js', joiner=joiner)
            return content and wrapper.format(content) or ''

        def get_libs():
            formatter = '<script src="{}"></script>'
            return get('libs', formatter)

        def get_styles():
            formatter = '<link rel="stylesheet" href="{}">'
            return get('styles', formatter)

        def get_head():
            return get('head')

        def get_tail():
            return get('tail')

        def get_content():
            return self.content

        def get_stdout():
            stdout = sys.stdout.getvalue()
            if stdout:
                sys.stdout.close()
                sys.stdout = io.StringIO()
            value = ''.join(
                list(composition.parts.parts.get('stdout', [])) +
                [stdout]
            )
            if value:
                return html.pre(zoom.tools.websafe(value) + '{*stdout*}')
            return '{*stdout*}'

        return dict(
            {'page_' + k: v for k, v in self.__dict__.items()},
            page_title=request.site.title,
            site_url=request.site.url,
            author=request.site.owner_name,
            css=get_css,
            content=get_content,
            js=get_js,
            head=get_head,
            tail=get_tail,
            styles=get_styles,
            libs=get_libs,
            alerts=get_alerts(request),
            stdout=get_stdout,
            theme=self.theme,
            theme_uri=self.theme_uri,
        )

    def render(self, request):
        """render page"""

        logger = logging.getLogger(__name__)
        logger.debug('rendering page')

        if self.title or self.subtitle or self.actions or self.search:
            full_page = Component(PageHeader(page=self), self.content)
        else:
            full_page = Component(self.content)
        self.content = full_page.render()

        app_theme = request.app.theme
        site_theme = zoom.system.site.theme
        self.theme = self.kwargs.get('theme', app_theme or site_theme)
        self.theme_uri = '/themes/' + self.theme

        zoom.render.add_helpers(
            zoom.forms.helpers(request),
            self.helpers(request),
        )

        template = zoom.tools.get_template(self.template, self.theme)

        return HTMLResponse(template)


page = Page  # pylint: disable=invalid-name
