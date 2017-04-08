"""
    zoom.forms
"""

import uuid

from zoom.helpers import tag_for
from zoom.fields import Fields
import zoom.html as html


def form_for(content=None, **kwargs):
    """returns a form with optional hidden values

    >>> print(form_for('test'))
    <form action="<dz:request_path>" enctype="application/x-www-form-urlencoded" id="zoom_form" method="POST" name="zoom_form">
    <input name="csrf_token" type="hidden" value="<dz:csrf_token>" />
    test
    </form>


    """

    params = kwargs.copy()
    name = params.pop('form_name', 'zoom_form')
    id = params.pop('id', 'zoom_form')
    method = params.pop('method', 'POST')
    action = params.pop('action', '<dz:request_path>')
    enctype = params.pop('enctype', 'application/x-www-form-urlencoded')

    t = []
    for key, value in params.items():
        t.append(
            html.hidden(name=key, value=value)
        )

    if method == 'POST':
        t.append(
            html.hidden(name='csrf_token', value=tag_for('csrf_token'))
        )

    return html.tag(
        'form',
        '\n' + '\n'.join(t + [content or '']) + '\n',
        action=action,
        name=name,
        id=name,
        method=method,
        enctype=enctype,
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


class Form(Fields):
    """An HTML form

    >>> from zoom.fields import TextField
    >>> form = Form(TextField("Name"))
    >>> print(form.edit())
    <form action="" enctype="application/x-www-form-urlencoded" id="zoom_form" method="POST" name="zoom_form">
    <input name="csrf_token" type="hidden" value="<dz:csrf_token>" />
    <div class="field">
      <div class="field_label">Name</div>
      <div class="field_edit"><table class="transparent">
        <tr>
            <td nowrap><input class="text_field" id="name" maxlength="40" name="name" size="40" type="text" value="" /></td>
            <td>
                <div class="hint"></div>
            </td>
        </tr>
    </table>
    </div>
    </div>
    <BLANKLINE>
    <BLANKLINE>
    """

    def __init__(self, *args, **kwargs):

        if len(args) == 1 and isinstance(args[0], (list, set, tuple)):
            self.fields = args[0]
        else:
            self.fields = list(args)

        self.enctype = 'application/x-www-form-urlencoded'
        for field in self.fields:
            try:
                if field.requires_multipart_form():
                    self.enctype = 'multipart/form-data'
            except AttributeError:
                pass

        self.action = kwargs.get('action', '')
        self.form_name = kwargs.get('form_name', 'zoom_form')
        self.method = kwargs.get('method', 'POST')

    def edit(self):
        fields = '\n  '.join([field.edit() for field in self.fields])
        return form(
            fields,
            action=self.action,
            id=self.form_name,
            form_name=self.form_name,
            method=self.method,
            enctype=self.enctype,
        )


def helpers(request):
    """form helpers"""
    return dict(
        form=form,
        csrf_token=csrf_token(request.session)
    )
