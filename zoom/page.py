"""
    zoom.page
"""

import logging

from zoom.component import composition#, requires
from zoom.components import as_actions
from zoom.response import HTMLResponse
from zoom.mvc import DynamicView
from zoom.utils import pp

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

            # def get(kind):
            #     try:
            #         return getattr(session, 'system_' + kind)
            #         # delattr(session, 'system_' + kind)
            #     except AttributeError:
            #         return []
            logger = logging.getLogger(__name__)
            logger.debug(pp(request.session.__dict__))

            pop = request.session.__dict__.pop

            success_alerts = pop('system_successes', [])
            if success_alerts:
                logger.debug('success: %r', success_alerts)
                successes = html.div(html.ul(success_alerts), Class='messages')
            else:
                successes = ''

            warning_alerts = pop('system_warnings', [])
            if warning_alerts:
                logger.debug('warnings: %r', warning_alerts)
                warnings = html.div(html.ul(warning_alerts), Class='warnings')
            else:
                warnings = ''

            error_alerts = pop('system_errors', [])
            # if error_alerts:
            #     logger.debug('errors: %r', error_alerts)
            errors = html.div(html.ul(error_alerts), Class='errors')
            # else:
            #     errors = ''

            return errors + warnings + successes

        def get(part, wrapper='{}'):
            parts = composition.parts.parts.get(part, [])
            return parts and '\n'.join(wrapper.format(part) for part in parts) or ''

        def get_css():
            wrapper = '<styles>\n{}\n</styles>'
            return get('css', wrapper)

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
            return 'test'

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
            request_path=request.path,
            author=request.site.owner_name,
            css=get_css(),
            js=get_js(),
            head=get_head(),
            tail=get_tail(),
            styles=get_styles(),
            libs=get_libs(),
            alerts=get_alerts(request),
        )

    def render(self, request):
        """render page"""

        def rendered(obj):
            """call the render method if necessary"""
            if hasattr(obj, 'render'):
                # return rendered(obj.render())
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

        page_header = PageHeader(page=self).render()
        save_content = self.content
        full_page = page_header + rendered(self.content)
        self.content = ''.join(full_page.parts['html'])
        content = zoom.render.apply_helpers(template, self, providers)
        self.content = save_content

        return HTMLResponse(content)


page = Page  # pylint: disable=invalid-name
