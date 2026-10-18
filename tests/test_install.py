import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'runtime'))
import install
import core
import gateway
import launcher
import rollback

spec = importlib.util.spec_from_file_location('omni_config', ROOT / 'scripts/configure_omniroute.py')
omni_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(omni_config)

class InstallTests(unittest.TestCase):
    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / 'absent'
            result = subprocess.run([sys.executable, str(ROOT / 'install.py'), '--dry-run', '--home', str(home)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(home.exists())
            self.assertEqual(len(json.loads(result.stdout)['models']), 7)

    def test_install_reinstall_backup_and_preserve_unrelated(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            original = home / '.claude/settings.json'
            original.parent.mkdir()
            original.write_text(json.dumps({'theme': 'light', 'env': {'MY_SETTING': 'keep-me'}, 'permissions': {'additionalDirectories': ['example-directory']}}))
            unrelated = home / '.gemini/config/skills/my-personal-skill/SKILL.md'
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text('unrelated custom skill')
            instructions = home / '.claude/CLAUDE.md'
            instructions.write_text('Existing user instructions.')
            native = home / '.local/bin/claude.exe'
            native.parent.mkdir(parents=True)
            native.write_text('test fixture only')
            instance = install.Installer(home)
            instance.install(native, update_path=False)
            initial_state = dict(instance.state)
            self.assertTrue(instance.state['complete'])
            installed = install.load(original)
            self.assertEqual(installed['theme'], 'light')
            self.assertEqual(installed['env']['MY_SETTING'], 'keep-me')
            self.assertEqual(installed['permissions']['additionalDirectories'], ['example-directory'])
            self.assertEqual(unrelated.read_text(), 'unrelated custom skill')
            self.assertIn('Existing user instructions.', instructions.read_text())
            router = install.load(home / '.claude/profiles/router/settings.json')
            self.assertEqual(len(router['modelPicker']['options']), 7)
            self.assertEqual({model.removesuffix('[1m]') for model in router['availableModels']}, set(core.MODELS))
            self.assertFalse((home / '.claude/profiles/router/.credentials.json').exists())
            self.assertTrue((home / '.claude/profiles/router/skills').is_dir())
            self.assertTrue(all(Path(row['backup']).is_file() for row in instance.state['files'] if row.get('backup')))
            repeat = install.Installer(home)
            repeat.install(native, update_path=False)
            repeated = install.load(original)
            self.assertEqual(len(repeated['hooks']['SessionStart']), 1)
            self.assertEqual(instructions.read_text().count('<!-- claude-openrouter-kit:start -->'), 1)
            self.assertEqual(unrelated.read_text(), 'unrelated custom skill')
            with patch.object(rollback, 'KIT', repeat.kit):
                rollback.rollback()
            self.assertEqual(unrelated.read_text(), 'unrelated custom skill')
            (instance.kit / 'installation.json').write_text(json.dumps(initial_state))
            with patch.object(rollback, 'KIT', instance.kit):
                rollback.rollback()
            self.assertEqual(install.load(original)['theme'], 'light')
            self.assertNotIn('hooks', install.load(original))
            self.assertEqual(instructions.read_text(), 'Existing user instructions.')
            self.assertEqual(unrelated.read_text(), 'unrelated custom skill')

    def test_external_link_refused(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as external:
            home = Path(temp)
            instance = install.Installer(home)
            with self.assertRaises(RuntimeError):
                instance.checked(Path(external) / 'settings.json')

    def test_omniroute_preserves_key_and_removes_duplicates(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home, package = root / 'home', root / 'package'
            (home / '.omniroute').mkdir(parents=True)
            package.mkdir()
            (package / 'package.json').write_text('{"name":"omniroute"}')
            (home / '.omniroute/.env').write_text('STORAGE_ENCRYPTION_KEY=synthetic-preserved-key\n')
            (package / '.env').write_text('STORAGE_ENCRYPTION_KEY=synthetic-ignored\nJWT_SECRET="synthetic#value"\nQUOTA_STORE_DRIVER=sqlite # comment\n')
            omni_config.configure(home, package)
            values = omni_config.entries((home / '.omniroute/.env').read_text())
            self.assertEqual(values['STORAGE_ENCRYPTION_KEY'], 'synthetic-preserved-key')
            self.assertEqual(omni_config.parsed(values['JWT_SECRET']), 'synthetic#value')
            self.assertEqual(omni_config.parsed(values['QUOTA_STORE_DRIVER']), 'sqlite')
            self.assertEqual(values['OMNIROUTE_SERVER_HOST'], '127.0.0.1')
            self.assertFalse(omni_config.entries((package / '.env').read_text()))
            self.assertTrue(list((home / '.omniroute/backups').glob('*/package.env')))
            count = len(list((home / '.omniroute/backups').iterdir()))
            omni_config.configure(home, package)
            self.assertEqual(len(list((home / '.omniroute/backups').iterdir())), count)

    def test_omniroute_existing_database_without_key_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home, package = root / 'home', root / 'package'
            (home / '.omniroute').mkdir(parents=True)
            (home / '.omniroute/storage.sqlite').write_text('synthetic existing database')
            package.mkdir()
            (package / 'package.json').write_text('{"name":"omniroute"}')
            with patch.dict(os.environ, {}, clear=True), self.assertRaises(RuntimeError):
                omni_config.configure(home, package)
            self.assertFalse((home / '.omniroute/.env').exists())

    def test_mac_keychain_secret_is_only_in_stdin(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / 'reference'
            fake = subprocess.CompletedProcess([], 0, b'', b'')
            with patch.object(core, 'os', SimpleNamespace(name='posix')), patch.object(core.sys, 'platform', 'darwin'), patch.object(core.subprocess, 'run', return_value=fake) as runner:
                core.save_secret(marker, 'sk-or-synthetic-test-key')
                args, kwargs = runner.call_args
                self.assertEqual(args[0], ['/usr/bin/security', '-i'])
                self.assertIn(b'sk-or-synthetic-test-key', kwargs['input'])
                self.assertNotIn('sk-or-', marker.read_text())

    def test_mac_descendant_scan_fails_closed(self):
        fake = subprocess.CompletedProcess([], 0, '11 10\n12 11\n20 1\n', '')
        with patch.object(launcher, 'os', SimpleNamespace(name='posix')), patch.object(launcher.subprocess, 'run', return_value=fake):
            self.assertEqual(launcher.children(10), [11, 12])
        with patch.object(launcher, 'os', SimpleNamespace(name='posix')), patch.object(launcher.subprocess, 'run', side_effect=OSError):
            self.assertIsNone(launcher.children(10))

if __name__ == '__main__':
    unittest.main()
