"""
    unittests.utils

    reusable functions
"""
import cgi
from io import BytesIO


def create_fieldstorage(mimetype, content, filename='test.pdf', name="file"):
    """return a cgi.FieldStorage like object"""
    headers = {
        'content-disposition': 'form-data; name="{}"; filename="{}"'.format(name, filename),
        'content-length': len(content),
        'content-type': mimetype
    }
    environ = {'REQUEST_METHOD': 'POST'}
    fp = BytesIO(content)
    return cgi.FieldStorage(fp=fp, headers=headers, environ=environ)
