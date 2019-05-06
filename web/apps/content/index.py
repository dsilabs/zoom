"""
    content.index
"""

import zoom
from zoom.mvc import View

from pages import load_page, get_pages

sitemap_tpl = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{pages}</urlset>"""

url_tpl = """    <url>
        <loc>{page.abs_path}</loc>
        <changefreq>daily</changefreq>
    </url>
"""

class MyView(View):
    """View"""

    @staticmethod
    def index():
        """app index"""
        return zoom.page(
            'Metrics and activity log and statistics will go here.',
            title='Overview'
        )

    def show(self, *args, **kwargs):
        """Show a page"""
        path = '/'.join(args) if args else None
        template = 'default'

        if path is None or path == 'content/index.html':
            path = ''
            template = 'index'
        else:
            path = '/'.join(path.split('/')[1:])

        content = load_page(path)
        if content:
            return zoom.page(content, template=template)
        return None

    def sitemap(self):
        """Return a sitemap"""
        content = sitemap_tpl.format(
            pages='\n'.join(
                url_tpl.format(page=page)
                for page in sorted(get_pages(), key=lambda a: a.path)
                if not page.exclude_from_sitemap
            )
        )
        return zoom.response.TextResponse(content)

view = MyView()
