"""
    zoom.forms
"""

import logging

import zoom
from zoom.helpers import url_for
from zoom.fields import Fields, MarkdownText, Hidden, Button
from zoom.utils import create_csrf_token
import zoom.html as html


logger = logging.getLogger(__name__)


def form_for(*args, **kwargs):
    """returns a form with optional hidden values

    >>> print(form_for('test'))
    <form action="<dz:request_path>" class="clearfix" enctype="application/x-www-form-urlencoded" id="zoom_form" method="POST" name="zoom_form">
    <input name="csrf_token" type="hidden" value="{{csrf_token}}" />
    test
    </form>

    """

    params = kwargs.copy()
    name = params.pop('form_name', 'zoom_form')
    _id = params.pop('id', 'zoom_form')
    method = params.pop('method', 'POST')
    action = params.pop('action', '<dz:request_path>')
    enctype = params.pop('enctype', 'application/x-www-form-urlencoded')
    classed = params.pop('classed', 'clearfix')

    t = []
    if method == 'POST':
        t.append(
            html.hidden(name='csrf_token', value='{{csrf_token}}')
        )

    content = []
    for arg in args:
        if arg:
            content.append(type(arg) == str and arg or arg.edit())
            if hasattr(arg, 'requires_multipart_form') and arg.requires_multipart_form():
                enctype = "multipart/form-data"

    for key, value in params.items():
        t.append(
            html.hidden(name=key, value=value)
        )

    return html.tag(
        'form',
        '\n' + '\n'.join(t + content) + '\n',
        action=action,
        name=name,
        id=_id,
        method=method,
        enctype=enctype,
        classed=classed,
    )


def form(content=None, **kwargs):
    """returns the first part of a form"""
    return form_for(content, **kwargs).replace('</form>', '')


def multipart_form_for(content, **keywords):
    """Returns a multipart form tag, surrounding specified content."""
    return form_for(content, enctype="multipart/form-data", **keywords)


def multipart_form(content, **kwargs):
    """Returns a multipart form tag."""
    return multipart_form_for(content, **kwargs).replace('</form>', '')


class Form(Fields):
    """An HTML form

    >>> from zoom.fields import TextField
    >>> form = Form(TextField("Name"))
    >>> print(form.edit())
    <form action="" class="clearfix" enctype="application/x-www-form-urlencoded" id="zoom_form" method="POST" name="zoom_form">
    <input name="csrf_token" type="hidden" value="{{csrf_token}}" />
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
    </form>
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
        self.form_id = kwargs.get('form_id', 'zoom_form')
        self.method = kwargs.get('method', 'POST')

    def edit(self):
        fields = '\n  '.join([field.edit() for field in self.fields])
        return form_for(
            fields,
            action=self.action,
            id=self.form_id,
            form_name=self.form_name,
            method=self.method,
            enctype=self.enctype,
        )


def delete_form(name, cancel=None):
    """produce a delete form"""
    css = """
    .delete-card {
        border: thin solid #ddd;
        margin: 10% auto;
        width: 50%;
        padding: 3em;
        background: white;
        box-shadow: 3px 3px 3px #ddd;
    }
    .delete-card p {
        font-size: 1.8rem;
    }
    @media (max-width: 600px) {
        .delete-card {
            padding: 1em;
            width: 100%;
        }
    }
    """
    return zoom.Component(
        html.div(
            Form(
                MarkdownText('Are you sure you want to delete **%s**?' % name),
                Hidden(name='confirm', value='no'),
                Button(
                    'Yes, I\'m sure.  Please delete.',
                    name='delete_button',
                    cancel=cancel or url_for('..')
                )
            ).edit(),
            classed='delete-card'
        ),
        css=css
    )


def get_form_token():
    request = zoom.system.request
    token = None
    if request and not getattr(request, 'form_token', None):
        token = request.form_token = create_csrf_token()
        logger.debug('new form_token created: %s', request.form_token)
    return token


def helpers(request):
    """form helpers"""
    return dict(
        form=form,
        csrf_token=get_form_token
    )
