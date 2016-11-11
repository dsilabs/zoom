# -*- coding: utf-8 -*-

"""
    zoom.response

    Various common web responses.

    Note:  We have chosen to use a dict for the headers even though
    technically the HTTP spec allows for multiple values by the same name
    because the uses cases for this seem to be very obscure and the benefits
    of not duplicating header entries that the dict provides seem to outweigh
    supporting obscure and generally not recommend use cases.  The only use
    case where this is more commonly used is in cookies, but we deal with that
    special case in the cookie module.
"""


from hashlib import md5
from collections import OrderedDict

from zoom.jsonz import dumps


class Response(object):
    """web response"""

    def __init__(self, content):
        self.status = '200 OK'
        self.headers = OrderedDict()
        self.content = content

    def render_doc(self):
        """Renders the payload"""
        return self.content

    def render(self):
        """Renders the entire response"""

        def render_headers(headers):
            """bring headers together into one string"""
            return (''.join(["%s: %s\n" % (header, value) for header, value in
                             headers.items()]))

        doc = self.render_doc()
        length_entry = {'Content-length': '%s' % len(doc)}
        headers = render_headers(
            OrderedDict(self.headers, **length_entry)
        ).encode('utf8')
        return b''.join([headers, b'\n', doc])

    def as_wsgi(self):
        """Render the entire response"""
        doc = self.render_doc()
        length_entry = [('Content-length', '%s' % len(doc))]
        return (
            self.status,
            list(self.headers.items()) + length_entry,
            doc
        )


class PNGResponse(Response):
    """PNG image response"""

    def __init__(self, content):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'image/png'


class PNGCachedResponse(PNGResponse):
    """Cached PNG image response"""

    def __init__(self, content, age=86400):
        PNGResponse.__init__(self, content)
        self.headers['Cache-Control'] = 'max-age={}'.format(age)
        self.headers['ETag'] = md5(content).hexdigest()[:9]


class JPGResponse(Response):
    """JPG image response"""

    def __init__(self, content):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'image/jpeg'


class GIFResponse(Response):
    """GIF image response"""

    def __init__(self, content):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'image/gif'


class TextResponse(Response):
    """Plan text response"""

    def __init__(self, content=''):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'text'
        self.headers['Cache-Control'] = 'no-cache'

    def render_doc(self):
        return self.content.encode('utf8')


class HTMLResponse(TextResponse):
    """
    HTML response

    >>> HTMLResponse('test123').render() == (
    ...     'Content-type: text/html\\n'
    ...     'Cache-Control: no-cache\\n'
    ...     'X-FRAME-OPTIONS: DENY\\n'
    ...     'Content-length: 7\\n\\n'
    ...     b'test123'
    ... )
    True

    >>> HTMLResponse('test123').as_wsgi() == (
    ...    '200 OK',
    ...    [
    ...       ('Content-type', 'text/html'),
    ...       ('Cache-Control', 'no-cache'),
    ...       ('X-FRAME-OPTIONS', 'DENY'),
    ...       ('Content-length', '7')
    ...    ],
    ...    b'test123'
    ... )
    True
    """

    def __init__(self, content=''):
        TextResponse.__init__(self, content)
        self.headers['Content-type'] = 'text/html'
        self.headers['Cache-Control'] = 'no-cache'
        self.headers['X-FRAME-OPTIONS'] = 'DENY'


class XMLResponse(Response):
    """XML response"""

    def __init__(self, content=''):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'text/xml'
        self.headers['Cache-Control'] = 'no-cache'

    def render_doc(self):
        doc = '<?xml version="1.0"?>%s' % self.content
        return doc.encode('utf8')


class JavascriptResponse(TextResponse):
    """Javascript response"""

    def __init__(self, content):
        TextResponse.__init__(self, content)
        self.headers['Content-type'] = 'application/javascript'


class JSONResponse(TextResponse):
    """JSON response"""

    def __init__(
        self,
        content,
        indent=4,
        sort_keys=True,
        ensure_ascii=False,
        **kwargs
    ):
        content = dumps(content, indent, sort_keys, ensure_ascii, **kwargs)
        TextResponse.__init__(self, content)
        self.headers['Content-type'] = 'application/json;charset=utf-8'


class CSSResponse(TextResponse):
    """CSS response"""

    def __init__(self, content):
        TextResponse.__init__(self, content)
        self.headers['Content-type'] = 'text/css;charset=utf-8'


class RedirectResponse(Response):
    """Redirect response"""

    def __init__(self, url):
        Response.__init__(self, '')
        self.status = '302 Found'
        self.headers['Location'] = url


class FileResponse(Response):
    """File download response"""

    def __init__(self, filename, content=None):
        Response.__init__(self, '')
        if content:
            self.content = content
        else:
            self.content = file(filename, 'rb').read()
        import os
        _, fileonly = os.path.split(filename)
        self.headers['Content-type'] = 'application/octet-stream'
        self.headers['Content-Disposition'] = \
                'attachment; filename="%s"' % fileonly
        self.headers['Cache-Control'] = 'no-cache'


class PDFResponse(FileResponse):
    """PDF file download response"""

    def __init__(self, filename, content=None):
        FileResponse.__init__(self, filename, content)
        self.headers['Content-type'] = 'application/pdf'
        del self.headers['Content-Disposition']
