"""
    test secrets CLI
"""

import io
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import zoom
import zoom.database
import zoom.utils
from zoom.cli.secrets import secrets
from zoom.encryption import generate_key, key_name
from zoom.secrets import get_secrets_store


class TestCliSecrets(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.site_path = os.path.join(self.tmpdir.name, 'site')
        os.makedirs(self.site_path)
        with open(os.path.join(self.site_path, 'site.ini'), 'w') as f:
            f.write('[site]\nname=TEST\n')

        self.secrets_path = os.path.join(self.tmpdir.name, 'secrets')
        os.makedirs(self.secrets_path)
        self.key_path = os.path.join(self.secrets_path, key_name)
        self.key = generate_key()
        with open(self.key_path, 'w') as f:
            f.write(self.key.decode())

        self._env_patcher = patch.dict(os.environ, {
            'ZOOM_SECRETS_PATH': self.secrets_path,
            'ZOOM_TEST_DATABASE_ENGINE': 'memory',
        })
        self._env_patcher.start()
        os.environ.pop(key_name.upper(), None)

        self.db = zoom.database.setup_test('memory')
        zoom.system.site = zoom.utils.Bunch(db=self.db)
        get_secrets_store().zap()

    def tearDown(self):
        self._env_patcher.stop()
        self.tmpdir.cleanup()

    def _fake_site(self, path=None):
        site = MagicMock()
        site.db = self.db

        def activate():
            zoom.system.site = site

        site.activate.side_effect = activate
        return site

    def invoke(self, *args, expect_success=None):
        """Run secrets CLI and return (exit_code, stdout, stderr)."""
        argv = ['zoom', 'secrets'] + list(args)
        if 'new-key' not in args and '--site' not in args:
            argv.extend(['--site', self.site_path])

        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(sys, 'argv', argv):
            with patch('zoom.cli.secrets.Site', side_effect=self._fake_site):
                with patch('sys.stdout', stdout):
                    with patch('sys.stderr', stderr):
                        code = 0
                        try:
                            secrets()
                        except SystemExit as exc:
                            code = 0 if exc.code in (None, 0) else exc.code

        if expect_success is True:
            self.assertEqual(code, 0, stderr.getvalue())
        elif expect_success is False:
            self.assertNotEqual(code, 0, stdout.getvalue())
        return code, stdout.getvalue(), stderr.getvalue()

    # --- new-key ---

    def test_new_key_creates_key(self):
        os.remove(self.key_path)
        code, out, _ = self.invoke('new-key', expect_success=True)
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(self.key_path))
        with open(self.key_path) as f:
            self.assertTrue(f.read().strip())
        self.assertIn(self.key_path, out)

    def test_new_key_no_force_fails(self):
        self.invoke('new-key', expect_success=False)

    def test_new_key_with_force_overwrites(self):
        with open(self.key_path) as f:
            old_key = f.read()
        code, _, _ = self.invoke('new-key', '--force', expect_success=True)
        self.assertEqual(code, 0)
        with open(self.key_path) as f:
            self.assertNotEqual(f.read(), old_key)

    # --- site validation ---

    def test_site_required(self):
        argv = ['zoom', 'secrets', 'list']
        with patch.object(sys, 'argv', argv):
            with patch('sys.stderr', io.StringIO()) as stderr:
                with self.assertRaises(SystemExit) as cm:
                    secrets()
        self.assertNotEqual(cm.exception.code, 0)

    def test_invalid_site_fails(self):
        code, _, err = self.invoke(
            'list', '--site', os.path.join(self.tmpdir.name, 'nope')
        )
        self.assertNotEqual(code, 0)
        self.assertIn('no Zoom site', err)

    # --- set / get / list ---

    def test_set_and_get_masked(self):
        self.invoke('set', 'api-key', 'super-secret', expect_success=True)
        code, out, _ = self.invoke('get', 'api-key', expect_success=True)
        self.assertEqual(out.strip(), '****')

    def test_get_reveal(self):
        self.invoke('set', 'api-key', 'super-secret', expect_success=True)
        _, out, _ = self.invoke(
            'get', 'api-key', '--reveal', expect_success=True
        )
        self.assertEqual(out.strip(), 'super-secret')

    def test_get_json_masked(self):
        self.invoke('set', 'api-key', 'super-secret', expect_success=True)
        _, out, _ = self.invoke(
            'get', 'api-key', '--json', expect_success=True
        )
        self.assertEqual(json.loads(out), {'api-key': '****'})

    def test_get_json_reveal(self):
        self.invoke('set', 'api-key', 'super-secret', expect_success=True)
        _, out, _ = self.invoke(
            'get', 'api-key', '--json', '--reveal', expect_success=True
        )
        self.assertEqual(json.loads(out), {'api-key': 'super-secret'})

    def test_get_missing(self):
        code, _, err = self.invoke('get', 'missing')
        self.assertNotEqual(code, 0)
        self.assertIn('not found', err)

    def test_list(self):
        self.invoke('set', 'a', '1', expect_success=True)
        self.invoke('set', 'b', '2', expect_success=True)
        _, out, _ = self.invoke('list', expect_success=True)
        names = out.strip().splitlines()
        self.assertEqual(sorted(names), ['a', 'b'])

    def test_list_json(self):
        self.invoke('set', 'a', '1', expect_success=True)
        self.invoke('set', 'b', '2', expect_success=True)
        _, out, _ = self.invoke('list', '--json', expect_success=True)
        self.assertEqual(sorted(json.loads(out)), ['a', 'b'])

    def test_set_from_stdin(self):
        argv = [
            'zoom', 'secrets', 'set', 'from-stdin', '-',
            '--site', self.site_path,
        ]
        with patch.object(sys, 'argv', argv):
            with patch('zoom.cli.secrets.Site', side_effect=self._fake_site):
                with patch('sys.stdin', io.StringIO('stdin-value\n')):
                    with patch('sys.stdout', io.StringIO()):
                        try:
                            secrets()
                        except SystemExit as exc:
                            self.assertIn(exc.code, (None, 0))
        _, out, _ = self.invoke(
            'get', 'from-stdin', '--reveal', expect_success=True
        )
        self.assertEqual(out.strip(), 'stdin-value')

    def test_set_quiet(self):
        _, out, _ = self.invoke(
            'set', 'q', 'v', '--quiet', expect_success=True
        )
        self.assertEqual(out, '')

    # --- exists ---

    def test_exists_true(self):
        self.invoke('set', 'x', '1', expect_success=True)
        code, out, _ = self.invoke('exists', 'x')
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), 'true')

    def test_exists_false(self):
        code, out, _ = self.invoke('exists', 'nope')
        self.assertEqual(code, 1)
        self.assertEqual(out.strip(), 'false')

    def test_exists_json(self):
        self.invoke('set', 'x', '1', expect_success=True)
        code, out, _ = self.invoke('exists', 'x', '--json')
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {'exists': True})

    # --- delete / rename / clear ---

    def test_delete(self):
        self.invoke('set', 'doomed', 'v', expect_success=True)
        self.invoke('delete', 'doomed', expect_success=True)
        code, _, _ = self.invoke('exists', 'doomed')
        self.assertEqual(code, 1)

    def test_rename(self):
        self.invoke('set', 'old', 'value', expect_success=True)
        self.invoke('rename', 'old', 'new', expect_success=True)
        code, _, _ = self.invoke('exists', 'old')
        self.assertEqual(code, 1)
        _, out, _ = self.invoke(
            'get', 'new', '--reveal', expect_success=True
        )
        self.assertEqual(out.strip(), 'value')

    def test_clear(self):
        self.invoke('set', 'a', '1', expect_success=True)
        self.invoke('set', 'b', '2', expect_success=True)
        self.invoke('clear', expect_success=True)
        _, out, _ = self.invoke('list', expect_success=True)
        self.assertEqual(out.strip(), '')

    # --- key options ---

    def test_key_option(self):
        other_key = generate_key().decode()
        self.invoke(
            'set', 'k', 'v', '--key', other_key, expect_success=True
        )
        _, out, _ = self.invoke(
            'get', 'k', '--reveal', '--key', other_key, expect_success=True
        )
        self.assertEqual(out.strip(), 'v')

    def test_key_file_option(self):
        key_file = os.path.join(self.tmpdir.name, 'extra.key')
        other_key = generate_key().decode()
        with open(key_file, 'w') as f:
            f.write(other_key)
        self.invoke(
            'set', 'k', 'v', '--key-file', key_file, expect_success=True
        )
        _, out, _ = self.invoke(
            'get', 'k', '--reveal', '--key-file', key_file, expect_success=True
        )
        self.assertEqual(out.strip(), 'v')

    def test_missing_key_fails(self):
        os.remove(self.key_path)
        os.environ.pop(key_name.upper(), None)
        code, _, err = self.invoke('list')
        self.assertNotEqual(code, 0)
        self.assertIn('key', err.lower())
