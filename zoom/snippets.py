"""
    zoom.snippets
"""

import zoom
import zoom.html as h


class SystemSnippet(zoom.utils.Record):
    """SystemSnippet

    A chunk of text (usually HTML) that can be rendered by
    placing the {{snippet}} tag in a document or template.

    >>> db = zoom.database.setup_test()
    >>> snippets = get_snippets(db)
    >>> snippets.delete(name='test')
    >>> snippets.find(name='test')
    []

    >>> t = snippets.put(Snippet(name='test', body='some text'))
    >>> snippets.find(name='test')
    [<SystemSnippet {'key': 'test', 'name': 'test', 'url': '/content/snippets/test', 'body': 'some text', 'link': '<a href="/content/snippets/test">test</a>'}>]

    """

    @property
    def link(self):
        """Return a link"""
        return h.a(self.name, href=self.url)

    @property
    def url(self):
        return '/content/snippets/' + self.key

    @property
    def key(self):
        return zoom.utils.id_for(self.name)

    def allows(self, user, action):
        """Item level policy"""
        return True


Snippet = SystemSnippet


def snippet(name, default='', variant=None):
    snippets = get_snippets()

    snippet = snippets.first(name=name, variant=variant)
    if snippet:
        snippet['impressions'] = snippet.get('impressions', 0) + 1
        snippets.put(snippet)
        result = snippet.body
    else:
        result = default

    return result

def get_snippets(db=None):
    return zoom.store_of(Snippet, db=db)
