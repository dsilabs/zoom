"""
Usage:
  zoom secrets list [options]
  zoom secrets get [options] <name>
  zoom secrets set [options] <name> <value>
  zoom secrets delete [options] <name>
  zoom secrets rename [options] <old> <new>
  zoom secrets exists [options] <name>
  zoom secrets clear [options]
  zoom secrets new-key [options]

Options:
  -h --help            Show this help message.
  --site=<path>        Path to site directory.
  -k --key=<val>       Encryption key.
  --key-file=<path>    Read encryption key from file.
  -f --force           Overwrite existing key when using new-key.
  --reveal             Reveal secret values (for get).
  --json               Output machine-readable JSON.
  --quiet              Suppress output messages.
"""
from docopt import docopt
import json
import sys
import os

from zoom.encryption import generate_key, get_key_pathname
from zoom.cli.common import finish
from zoom.cli.utils import is_site_dir
from zoom.sites import Site
from zoom.secrets import get_secrets, get_secrets_store, SecretsKeyMissingException
from zoom.database import DatabaseException


def _resolve_site_path(args):
    site_path = args.get('--site')
    if not site_path:
        finish(True, 'Error: --site is required')
    site_path = os.path.abspath(os.path.expanduser(site_path))
    if not is_site_dir(site_path):
        finish(True, 'Error: no Zoom site at "%s"' % site_path)
    return site_path


def _resolve_key(args):
    key = args.get('--key')
    if args.get('--key-file'):
        try:
            with open(args['--key-file']) as f:
                key = f.read().strip()
        except Exception as e:
            finish(True, f'Error reading key file: {e}')
    return key


def secrets():
    args = docopt(__doc__)

    # new-key: generate and save encryption key to ZOOM_SECRETS_PATH
    if args['new-key']:
        key_path = get_key_pathname()
        key_dir = os.path.dirname(key_path)
        if key_dir and not os.path.isdir(key_dir):
            try:
                os.makedirs(key_dir, exist_ok=True)
            except OSError as e:
                finish(True, f'Error creating secrets directory {key_dir}: {e}')
        if os.path.isfile(key_path) and not args['--force']:
            finish(True, f'Secrets key already exists at {key_path}; use --force to overwrite')
        newkey = generate_key().decode()
        try:
            with open(key_path, 'w') as f:
                f.write(newkey)
        except OSError as e:
            finish(True, f'Error writing key file {key_path}: {e}')
        print(f'New secrets key generated and saved to {key_path}')
        sys.exit(0)

    site_path = _resolve_site_path(args)
    site = Site(site_path)
    site.activate()

    key = _resolve_key(args)

    try:
        store = get_secrets_store()
        secrets_obj = get_secrets(key, store)
    except SecretsKeyMissingException as e:
        finish(True, str(e))

    cmd = None
    for c in ('list', 'get', 'set', 'delete', 'rename', 'exists', 'clear'):
        if args[c]:
            cmd = c
            break

    try:
        if cmd == 'list':
            names = secrets_obj.keys()
            if args['--json']:
                print(json.dumps(names))
            else:
                for n in names:
                    print(n)

        elif cmd == 'get':
            name = args['<name>']
            val = secrets_obj.get(name)
            if val is None:
                finish(True, f'secret not found: {name}')
            if args['--json']:
                out_val = val if args['--reveal'] else '****'
                print(json.dumps({name: out_val}))
            elif not args['--quiet']:
                print(val if args['--reveal'] else '****')

        elif cmd == 'set':
            name = args['<name>']
            value = args['<value>']
            if value == '-':
                value = sys.stdin.read().rstrip('\n')
            secrets_obj.set(name, value)
            if not args['--quiet']:
                print(f'secret set: {name}')

        elif cmd == 'delete':
            name = args['<name>']
            secrets_obj.delete(name)
            if not args['--quiet']:
                print(f'secret deleted: {name}')

        elif cmd == 'rename':
            old = args['<old>']
            new = args['<new>']
            secrets_obj.rename(old, new)
            if not args['--quiet']:
                print(f'secret renamed: {old} -> {new}')

        elif cmd == 'exists':
            name = args['<name>']
            exists = secrets_obj.exists(name)
            if args['--json']:
                print(json.dumps({'exists': exists}))
            elif not args['--quiet']:
                print('true' if exists else 'false')
            sys.exit(0 if exists else 1)

        elif cmd == 'clear':
            secrets_obj.clear()
            if not args['--quiet']:
                print('all secrets cleared')

        else:
            finish(True, 'No command specified', __doc__)
    except SecretsKeyMissingException as e:
        finish(True, str(e))
    except DatabaseException as e:
        finish(True, f'Database error: {e}')
    except Exception as e:
        finish(True, f'Error: {e}')
