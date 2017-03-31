"""
    zoom.page
"""

import os

from zoom.components import as_actions
from zoom.fill import dzfill
from zoom.response import HTMLResponse
from zoom.mvc import DynamicView

import zoom.helpers
import zoom.apps
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
        self.actions = []
        self.search = None
        self.__dict__.update(kwargs)
        self.args = args
        self.kwargs = kwargs

    def helpers(self, request):
        """provide page helpers"""
        return dict(
            {'page_' + k: v for k, v in self.__dict__.items()},
            title=request.site.name,
            site_url=request.site.url,
            request_path=request.path,
            css='',
            js='',
            head='',
            tail='',
            styles='',
            libs='',
        )

    def render(self, request):
        """render page"""

        template = request.site.get_template(self.template)

        providers = [
            zoom.helpers.__dict__,
            request.site.helpers(),
            request.user.helpers(),
            zoom.apps.helpers(request),
            self.helpers(request),
        ]

        page_header = PageHeader(page=self).render()
        save_content = self.content
        full_page = page_header + self.content
        self.content = ''.join(full_page.parts['html'])
        content = zoom.render.apply_helpers(template, self, providers)
        self.content = save_content
        
        return HTMLResponse(content)



page = Page  # pylint: disable=invalid-name
