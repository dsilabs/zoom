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

import zoom
import zoom.templates
import zoom.components.instances
from zoom.jsonz import dumps


class Response(object):
    """web response

    >>> response = Response(b'this is it')
    >>> response.render()
    b'Status: 200 OK\\nContent-length: 10\\n\\nthis is it'
    >>> response.as_wsgi()
    ('200 OK', [('Content-length', '10')], b'this is it')
    """

    def __init__(self, content=b'', status='200 OK', headers=None):
        self.content = content
        self.status = status
        self.headers = OrderedDict(headers or {})
        self.cookie = {}

    def render_doc(self):
        """Renders the payload"""
        return self.content

    def render(self):
        """Renders the entire response"""

        status, headers, doc = self.as_wsgi()
        start = (
            ''.join(
                '{}: {}\n'.format(k, v) for k, v in
                [('Status', status)] + headers
            )
        ).encode('utf8')

        return b''.join([start, b'\n', doc])

    def as_wsgi(self):
        """Render the entire response"""
        doc = self.render_doc()
        headers = list(self.headers.items())
        headers.extend(('Set-Cookie', morsel.OutputString())
                for morsel
                in self.cookie.values())
        headers.append(('Content-length', '%s' % len(doc)))
        return (
            self.status,
            headers,
            doc
        )


class BinaryResponse(Response):
    """Generic binary response

    use max_age=0 to avoid caching

    >>> response = BinaryResponse(b'binary data')
    >>> expected = (
    ...     b'Status: 200 OK\\n'
    ...     b'Content-type: application/octet-stream\\n'
    ...     b'Cache-Control: max-age=86400\\n'
    ...     b'ETag: e1a49b59e\\n'
    ...     b'Content-length: 11\\n\\n'
    ...     b'binary data'
    ... )
    >>> response.render() == expected
    True

    """

    def __init__(self, content, max_age=86400):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'application/octet-stream'
        if max_age:
            self.headers['Cache-Control'] = 'max-age={}'.format(max_age)
            self.headers['ETag'] = md5(content).hexdigest()[:9]


class TTFResponse(Response):
    """True Type Font response

    >>> response = TTFResponse(b'myfont')
    >>> expected = (
    ...     b'Status: 200 OK\\n'
    ...     b'Content-type: application/font-sfnt\\n'
    ...     b'Cache-Control: max-age=86400\\n'
    ...     b'ETag: 794c8f9c8\\n'
    ...     b'Content-length: 6\\n\\n'
    ...     b'myfont'
    ... )
    >>> response.render() == expected
    True
    """

    def __init__(self, content, max_age=86400):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'application/font-sfnt'
        self.headers['Cache-Control'] = 'max-age={}'.format(max_age)
        self.headers['ETag'] = md5(content).hexdigest()[:9]


class WOFFResponse(Response):
    """Web Open Font Format response

    >>> response = WOFFResponse(b'myfont')
    >>> expected = (
    ...     b'Status: 200 OK\\n'
    ...     b'Content-type: application/font-woff\\n'
    ...     b'Cache-Control: max-age=86400\\n'
    ...     b'ETag: 794c8f9c8\\n'
    ...     b'Content-length: 6\\n\\n'
    ...     b'myfont'
    ... )
    >>> response.render() == expected
    True
    """

    def __init__(self, content, max_age=86400):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'application/font-woff'
        self.headers['Cache-Control'] = 'max-age={}'.format(max_age)
        self.headers['ETag'] = md5(content).hexdigest()[:9]


class WOFF2Response(Response):
    """Web Open Font 2 Format response

    >>> response = WOFF2Response(b'myfont')
    >>> expected = (
    ...     b'Status: 200 OK\\n'
    ...     b'Content-type: font/woff2\\n'
    ...     b'Cache-Control: max-age=86400\\n'
    ...     b'ETag: 794c8f9c8\\n'
    ...     b'Content-length: 6\\n\\n'
    ...     b'myfont'
    ... )
    >>> response.render() == expected
    True
    """

    def __init__(self, content, max_age=86400):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'font/woff2'
        self.headers['Cache-Control'] = 'max-age={}'.format(max_age)
        self.headers['ETag'] = md5(content).hexdigest()[:9]


class PNGResponse(Response):
    """PNG image response

    >>> response = PNGResponse(b'myimage')
    >>> expected = (
    ...     b'Status: 200 OK\\n'
    ...     b'Content-type: image/png\\n'
    ...     b'Cache-Control: max-age=86400\\n'
    ...     b'ETag: b1a9acaf2\\n'
    ...     b'Content-length: 7\\n\\n'
    ...     b'myimage'
    ... )
    >>> response.render() == expected
    True
    """

    def __init__(self, content, max_age=86400):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'image/png'
        self.headers['Cache-Control'] = 'max-age={}'.format(max_age)
        self.headers['ETag'] = md5(content).hexdigest()[:9]


class ICOResponse(Response):
    """ICO image response

    >>> response = ICOResponse(b'myicon')
    >>> expected = (
    ...     b'Status: 200 OK\\n'
    ...     b'Content-type: image/x-icon\\n'
    ...     b'Cache-Control: max-age=86400\\n'
    ...     b'ETag: 78d2485ff\\n'
    ...     b'Content-length: 6\\n\\n'
    ...     b'myicon'
    ... )
    >>> response.render() == expected
    True
    """

    def __init__(self, content, max_age=86400):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'image/x-icon'
        self.headers['Cache-Control'] = 'max-age={}'.format(max_age)
        self.headers['ETag'] = md5(content).hexdigest()[:9]

    def render_doc(self):
        """Renders the payload"""
        return self.content


class JPGResponse(Response):
    """JPG image response

    >>> response = JPGResponse(b'myimage')
    >>> expected = (
    ...     b'Status: 200 OK\\n'
    ...     b'Content-type: image/jpeg\\n'
    ...     b'Content-length: 7\\n\\n'
    ...     b'myimage'
    ... )
    >>> response.render() == expected
    True
    """

    def __init__(self, content):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'image/jpeg'


class GIFResponse(Response):
    """GIF image response

    >>> response = GIFResponse(b'myimage')
    >>> expected = (
    ...     b'Status: 200 OK\\n'
    ...     b'Content-type: image/gif\\n'
    ...     b'Content-length: 7\\n\\n'
    ...     b'myimage'
    ... )
    >>> response.render() == expected
    True
    """

    def __init__(self, content):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'image/gif'


class SVGResponse(Response):
    """
    SVG Response
    Returns a response as an SVG

    >>> response = SVGResponse(b'pretend SVG')
    >>> response.render()
    b'Status: 200 OK\\nContent-type: image/svg+xml\\nContent-length: 11\\n\\npretend SVG'

    """

    def __init__(self, content):
        Response.__init__(self, content)
        self.headers['Content-type'] = "image/svg+xml"


class MP4Response(Response):
    """
    MP4 Response
    Returns a response as an mp4 video

    >>> response = MP4Response(b'pretend MP4')
    >>> response.render()
    b'Status: 200 OK\\nContent-type: video/mp4\\nContent-length: 11\\n\\npretend MP4'

    """

    def __init__(self, content):
        Response.__init__(self, content)
        self.headers['Content-type'] = "video/mp4"


class TextResponse(Response):
    """Plan text response

    >>> response = TextResponse('mytext')
    >>> expected = (
    ...     b'Status: 200 OK\\n'
    ...     b'Content-type: text\\n'
    ...     b'Cache-Control: no-cache\\n'
    ...     b'Content-length: 6\\n\\n'
    ...     b'mytext'
    ... )
    >>> response.render() == expected
    True
    """

    def __init__(self, content='', status='200 OK'):
        Response.__init__(self, content, status)
        self.headers['Content-type'] = 'text'
        self.headers['Cache-Control'] = 'no-cache'

    def render_doc(self):
        """Renders the payload"""
        return self.content.encode('utf8')


class HTMLResponse(TextResponse):
    """
    HTML response

    >>> HTMLResponse('test123').render() == (
    ...     b'Status: 200 OK\\n'
    ...     b'Content-type: text/html\\n'
    ...     b'Cache-Control: no-cache\\n'
    ...     b'X-FRAME-OPTIONS: DENY\\n'
    ...     b'Content-length: 7\\n\\n'
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

    def __init__(self, content='', status='200 OK'):
        TextResponse.__init__(self, content)
        self.headers['Content-type'] = 'text/html'
        self.headers['Cache-Control'] = 'no-cache'
        self.headers['X-FRAME-OPTIONS'] = 'DENY'
        self.status = status


class XMLResponse(Response):
    """XML response

    >>> response = XMLResponse('myxml')
    >>> expected = (
    ...     b'Status: 200 OK\\n'
    ...     b'Content-type: text/xml\\n'
    ...     b'Cache-Control: no-cache\\n'
    ...     b'Content-length: 26\\n\\n'
    ...     b'<?xml version="1.0"?>myxml'
    ... )
    >>> response.render() == expected
    True
    """

    def __init__(self, content=''):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'text/xml'
        self.headers['Cache-Control'] = 'no-cache'

    def render_doc(self):
        doc = '<?xml version="1.0"?>%s' % self.content
        return doc.encode('utf8')


class JavascriptResponse(Response):
    """Javascript response

    >>> response = JavascriptResponse(b'myjs')
    >>> expected = (
    ...     b'Status: 200 OK\\n'
    ...     b'Content-type: application/javascript\\n'
    ...     b'Cache-Control: max-age=86400\\n'
    ...     b'ETag: 8be4a11f3\\n'
    ...     b'Content-length: 4\\n\\n'
    ...     b'myjs'
    ... )
    >>> response.render() == expected
    True
    """

    def __init__(self, content, max_age=86400):
        TextResponse.__init__(self, content)
        self.headers['Content-type'] = 'application/javascript'
        self.headers['Cache-Control'] = 'max-age={}'.format(max_age)
        self.headers['ETag'] = md5(content).hexdigest()[:9]


class JSONResponse(TextResponse):
    """JSON response

    >>> response = JSONResponse('myjson')
    >>> expected = (
    ...     b'Status: 200 OK\\n'
    ...     b'Content-type: application/json;charset=utf-8\\n'
    ...     b'Cache-Control: no-cache\\n'
    ...     b'Content-length: 8\\n\\n'
    ...     b'"myjson"'
    ... )
    >>> response.render() == expected
    True
    """

    def __init__(
            self,
            content,
            indent=4,
            sort_keys=True,
            ensure_ascii=False,
            status='200 OK',
            **kwargs
    ):
        content = dumps(
            content,
            indent=indent,
            sort_keys=sort_keys,
            ensure_ascii=ensure_ascii,
            **kwargs
        )
        TextResponse.__init__(self, content, status=status)
        self.headers['Content-type'] = 'application/json;charset=utf-8'


class CSSResponse(Response):
    """CSS response

    >>> response = CSSResponse(b'mycss')
    >>> expected = (
    ...     b'Status: 200 OK\\n'
    ...     b'Content-type: text/css;charset=utf-8\\n'
    ...     b'Cache-Control: max-age=86400\\n'
    ...     b'ETag: 12a586855\\n'
    ...     b'Content-length: 5\\n\\n'
    ...     b'mycss'
    ... )
    >>> response.render() == expected
    True
    """

    def __init__(self, content, max_age=86400):
        TextResponse.__init__(self, content)
        self.headers['Content-type'] = 'text/css;charset=utf-8'
        self.headers['Cache-Control'] = 'max-age={}'.format(max_age)
        self.headers['ETag'] = md5(content).hexdigest()[:9]


class RedirectResponse(TextResponse):
    """Redirect response

    >>> response = RedirectResponse('/')
    >>> response.as_wsgi()
    ('302 Found', [('Location', '/'), ('Content-length', '0')], b'')
    """

    def __init__(self, url):
        Response.__init__(self, '')
        self.status = '302 Found'
        self.headers['Location'] = url


class FileResponse(Response):
    """File download response

    >>> response = FileResponse('file.txt', content=b'mydata')
    >>> expected = (
    ...     b'Status: 200 OK\\n'
    ...     b'Content-type: application/octet-stream\\n'
    ...     b'Content-Disposition: attachment; filename="file.txt"\\n'
    ...     b'Cache-Control: no-cache\\n'
    ...     b'Content-length: 6\\n\\n'
    ...     b'mydata'
    ... )
    >>> response.render() == expected
    True
    """

    def __init__(self, filename, content=None):
        Response.__init__(self)
        if content:
            self.content = content
        else:
            self.content = open(filename, 'rb').read()
        import os
        _, fileonly = os.path.split(filename)
        self.headers['Content-type'] = 'application/octet-stream'
        self.headers['Content-Disposition'] = \
                'attachment; filename="%s"' % fileonly
        self.headers['Cache-Control'] = 'no-cache'


class PDFResponse(FileResponse):
    """PDF file download response

    >>> response = PDFResponse('file.pdf', content=b'mydata')
    >>> expected = (
    ...     b'Status: 200 OK\\n'
    ...     b'Content-type: application/pdf\\n'
    ...     b'Cache-Control: no-cache\\n'
    ...     b'Content-length: 6\\n\\n'
    ...     b'mydata'
    ... )
    >>> response.render() == expected
    True
    """
    def __init__(self, filename, content=None):
        FileResponse.__init__(self, filename, content)
        self.headers['Content-type'] = 'application/pdf'
        del self.headers['Content-Disposition']


class SiteNotFoundResponse(HTMLResponse):
    """Site 404 Not Found response

    >>> request = zoom.utils.Bunch(
    ...     protocol='http',
    ...     host='localhost',
    ...     path='/',
    ...     ip_address='127.0.0.1',
    ...     module='index',
    ...     request_id=1234,
    ...     elapsed=0.01,
    ... )
    >>> response = SiteNotFoundResponse(request)
    >>> 'ZoomFoundry' in str(response.render())
    True
    """

    def __init__(self, request):
        content = zoom.components.instances.get_info_page(request)
        HTMLResponse.__init__(self, content, status='404 Not Found')
