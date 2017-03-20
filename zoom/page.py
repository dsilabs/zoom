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
    def action_items(self):
        return as_actions(self.model.actions)

    @property
    def search_box(self):
        if self.search == None:
            return ''
        else:
            search_box = SearchBox(value=self.model.search)
            return ''.join(search_box.render().parts['html'])


class Page(object):
    """a web page"""

    def __init__(self, content, *args, **kwargs):
        self.content = content
        self.theme = 'default'
        self.template = 'default'
        self.subtitle = ''
        self.actions = []
        self.search = None
        self.__dict__.update(kwargs)
        self.args = args
        self.kwargs = kwargs

    def helpers(self):
        """provide helpers"""
        return {'page_' + k: v for k, v in self.__dict__.items()}

    def render(self, request):
        """render page"""

        def not_found(name):
            """what happens when a helper is not found"""
            def missing_helper(*args, **kwargs):
                """provide some info for missing helpers"""
                parts = ' '.join(
                    [name] +
                    ['{!r}'.format(a) for a in args] +
                    ['{}={!r}'.format(k, v) for k, v in kwargs.items()]
                )
                return '&lt;dz:{}&gt; missing'.format(
                    parts,
                )
            return missing_helper

        def filler(helpers):
            """callback for filling in templates"""
            def _filler(name, *args, **kwargs):
                """handle the details of filling in templates"""

                if hasattr(self, name):
                    attr = getattr(self, name)
                    if callable(attr):
                        repl = attr(self, *args, **kwargs)
                    else:
                        repl = attr
                    return dzfill(repl, _filler)

                helper = helpers.get(name, not_found(name))
                if callable(helper):
                    repl = helper(*args, **kwargs)
                else:
                    repl = helper
                return dzfill(repl, _filler)
            return _filler

        helpers = {}
        helpers.update(zoom.helpers.__dict__)
        helpers.update(request.site.helpers())
        helpers.update(self.helpers())
        helpers.update(zoom.apps.helpers(request))
        helpers.update(dict(
            title=request.site.name,
            site_url=request.site.url,
            request_path=request.path,
            css='',
            js='',
            head='',
            tail='',
            styles='',
            libs='',
        ))

        template = 'default'
        theme_path = request.site.theme_path
        filename = os.path.join(theme_path, template + '.html')

        with open(filename) as reader:
            template = reader.read()
        page_header = PageHeader(self).render()
        save_content = self.content
        full_page = page_header + self.content
        self.content = ''.join(full_page.parts['html'])
        content = dzfill(template, filler(helpers))
        self.content = save_content
        
        return HTMLResponse(content)


page = Page  # pylint: disable=invalid-name
