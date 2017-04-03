"""
    zoom.forms
"""

import uuid

from zoom.helpers import tag_for
import zoom.html as html


def form_for(content=None, **kwargs):
    """returns a form with optional hidden values"""

    name = kwargs.get('form_name', 'zoom_form')
    method = kwargs.pop('method', 'POST')
    action = kwargs.pop('action', '<dz:request_path>')

    t = []
    for key, value in kwargs.items():
        t.append(
            html.hidden(name=key, value=value)
        )

    if method == 'POST':
        t.append(
            html.hidden(name='csrf_token', value=tag_for('csrf_token'))
        )

    return html.tag(
        'form',
        ''.join(t + [content or '']),
        action=action,
        name=name,
        id=name,
        method=method,
    )


def form(content=None, **kwargs):
    """returns the first part of a form"""
    return form_for(content, **kwargs).replace('</form>', '')


def multipart_form_for(content, **keywords):
    """Returns a multipart form tag, surrounding specified content."""
    return form_for(content, enctype="multipart/form-data", **kwargs)


def multipart_form(content, **kwargs):
    """Returns a multipart form tag."""
    return multipart_form_for(content, **kwargs).replace('</form>', '')


def csrf_token(session):
    """generate a csrf token"""
    if not hasattr(session, 'csrf_token'):
        session.csrf_token = uuid.uuid4().hex
    return session.csrf_token


def helpers(request):
    """form helpers"""
    return dict(
        form=form,
        csrf_token=csrf_token(request.session)
    )
