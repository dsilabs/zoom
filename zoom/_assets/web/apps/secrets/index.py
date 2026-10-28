"""
    secrets index
"""

import html

import zoom
import zoom.fields as f
import zoom.validators as v
from zoom.alerts import error
from zoom.tools import redirect_to

from zoom.encryption import (
    generate_key,
    get_encryption_key,
    get_key_pathname,
    get_secrets_path,
    key_name,
)
from zoom.secrets import (
    Secret,
    SecretsKeyMissingException,
    get_secrets_store,
)


class SecretField(f.MemoField):
    """Secret Field"""

    def show(self):
        return ''

    def display_value(self):
        return '*' * len(self.value)

    def as_searchable(self):
        return set()


def secret_fields():
    result = f.Fields(
        f.TextField('Name', v.required),
        f.MemoField('Description', v.required),
        SecretField('Value', v.required, browse=False, editable=False),
        f.DateField('Expiry', hint='optional'),
    )
    if zoom.system.request.route[-1] == 'edit':
        del result.fields[2]
    return result


def key_is_configured():
    return bool(get_encryption_key())


def setup_content():
    """HTML explaining how to configure the encryption key"""
    key_file = get_key_pathname()
    secrets_path = get_secrets_path()
    env_name = key_name.upper()
    new_key = generate_key().decode()
    install_cmd = (
        "mkdir -p {path} && "
        "echo '{key}' > {file} && "
        "chmod 600 {file}"
    ).format(path=secrets_path, key=new_key, file=key_file)

    return (
        """
            <h3>Configuration Required</h3>
            This site does not currently have an encryption key available.
            Secrets cannot be stored until you provide a key
        """
        ' by saving the key in '
        'the file named <code>{key_file}</code> (recommended) or by '
        'providing the key in an environment variable named <code>{env_name}</code>.'
        '<br><br>'
        'By default Zoom looks in <code>~/.zoom/secrets</code>. '
        'For production, set <code>ZOOM_SECRETS_PATH=/run/secrets</code> '
        '(or another service-managed path) and install the key as the service user.'
        '<br><br>'
        'Current secrets path: <code>{secrets_path}</code> '
        '(override with <code>ZOOM_SECRETS_PATH</code>).'
        '<br><br>'
        'You can also run <code>zoom secrets new-key</code> to generate and write a key file.'
        '<br><br>'
        '<h4>Install with one command</h4>'
        'Copy and paste this into a terminal (runs as your user; no sudo required):'
        '<br><br>'
        '<div style="display:flex;gap:0.5rem;align-items:flex-start;">'
        '<pre id="zoom-secrets-install-cmd" '
        'style="flex:1;margin:0;white-space:pre-wrap;word-break:break-all;">{cmd}</pre>'
        '<button type="button" class="btn btn-secondary btn-sm" '
        'id="zoom-secrets-copy-btn" onclick="zoomSecretsCopyInstallCmd()">'
        'Copy</button>'
        '</div>'
        '<div id="zoom-secrets-copy-status" style="margin-top:0.5rem;font-size:0.9em;"></div>'
        '<br>'
        'Key only (if you prefer to place it yourself): <code>{key}</code>'
        '<script>'
        'function zoomSecretsCopyInstallCmd(){{'
        '  var el = document.getElementById("zoom-secrets-install-cmd");'
        '  var status = document.getElementById("zoom-secrets-copy-status");'
        '  var btn = document.getElementById("zoom-secrets-copy-btn");'
        '  var text = el ? el.textContent : "";'
        '  function ok(){{'
        '    if (status) status.textContent = "Copied to clipboard.";'
        '    if (btn) {{ btn.textContent = "Copied"; setTimeout(function(){{ btn.textContent = "Copy"; }}, 2000); }}'
        '  }}'
        '  function fail(){{'
        '    if (status) status.textContent = "Could not copy automatically. Select the command and copy it manually.";'
        '  }}'
        '  if (navigator.clipboard && navigator.clipboard.writeText) {{'
        '    navigator.clipboard.writeText(text).then(ok).catch(fail);'
        '  }} else {{'
        '    try {{'
        '      var range = document.createRange();'
        '      range.selectNodeContents(el);'
        '      var sel = window.getSelection();'
        '      sel.removeAllRanges();'
        '      sel.addRange(range);'
        '      document.execCommand("copy");'
        '      sel.removeAllRanges();'
        '      ok();'
        '    }} catch (e) {{ fail(); }}'
        '  }}'
        '}}'
        '</script>'
    ).format(
        key_file=html.escape(key_file),
        env_name=html.escape(env_name),
        secrets_path=html.escape(secrets_path),
        cmd=html.escape(install_cmd),
        key=html.escape(new_key),
    )


def setup_page(title='Secrets Setup'):
    return zoom.page(setup_content(), title=title)


class SecretsView(zoom.collect.CollectionView):

    def index(self, q='', *args, **kwargs):
        if not key_is_configured():
            return setup_page()
        return super().index(q, *args, **kwargs)

    def new(self, *args, **kwargs):
        if not key_is_configured():
            error(
                'Secrets encryption key is not configured. '
                'Set up a key before creating secrets.'
            )
            return setup_page()
        return super().new(*args, **kwargs)


class SecretsController(zoom.collect.CollectionController):

    def create_button(self, *args, **data):
        if not key_is_configured():
            error(
                'Secrets encryption key is not configured. '
                'Set up a key before creating secrets.'
            )
            return redirect_to(self.collection.url)
        try:
            return super().create_button(*args, **data)
        except SecretsKeyMissingException:
            error(
                'Secrets encryption key is not configured. '
                'Set up a key before creating secrets.'
            )
            return redirect_to(self.collection.url)


main = zoom.collection_of(
    secret_fields,
    store=get_secrets_store(),
    model=Secret,
    view=SecretsView,
    controller=SecretsController,
    url='/secrets'
)
