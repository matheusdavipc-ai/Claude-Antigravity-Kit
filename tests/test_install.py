import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'runtime'))
import install
import core
import rollback


def fixture_native(home):
    native = home / '.local/bin/claude.exe'
    native.parent.mkdir(parents=True, exist_ok=True)
    native.write_text('test fixture only')
    return native


def legacy_hook(home, matcher=''):
    script = str(home.resolve() / '.claude/launcher/runtime/hook.py')
    return {'matcher': matcher, 'hooks': [{'type': 'command', 'command': sys.executable, 'args': [script], 'timeout': 15}]}


class InstallTests(unittest.TestCase):
    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / 'absent'
            result = subprocess.run([sys.executable, str(ROOT / 'install.py'), '--dry-run', '--home', str(home)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(home.exists())
            plan = json.loads(result.stdout)
            self.assertEqual(plan['profile'], '.claude')
            self.assertNotIn('router', result.stdout)

    def test_install_reinstall_backup_and_preserve_unrelated(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            original = home / '.claude/settings.json'
            original.parent.mkdir()
            original.write_text(json.dumps({'theme': 'light', 'model': 'fable', 'availableModels': ['sonnet', 'opus', 'claude-sonnet-5', 'nvidia/nemotron-3.5-lightning:free'], 'env': {'MY_SETTING': 'keep-me', 'ANTHROPIC_DEFAULT_HAIKU_MODEL': 'claude-sonnet-5-5', 'ANTHROPIC_DEFAULT_FABLE_MODEL': 'claude-opus-5-5', 'ANTHROPIC_DEFAULT_FABLE_MODEL_NAME':'Legacy Opus'}, 'permissions': {'additionalDirectories': ['example-directory']}}))
            unrelated = home / '.gemini/config/skills/my-personal-skill/SKILL.md'
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text('unrelated custom skill')
            instructions = home / '.claude/CLAUDE.md'
            instructions.write_text('Existing user instructions.')
            native = fixture_native(home)
            instance = install.Installer(home)
            instance.install(native, update_path=False)
            initial_state = dict(instance.state)
            self.assertTrue(instance.state['complete'])
            installed = install.load(original)
            self.assertEqual(installed['theme'], 'light')
            self.assertEqual(installed['env']['MY_SETTING'], 'keep-me')
            self.assertEqual(installed['env']['ANTHROPIC_DEFAULT_OPUS_MODEL'], 'claude-opus-5-5')
            self.assertFalse(any(k.startswith('ANTHROPIC_DEFAULT_FABLE_MODEL') for k in installed['env']))
            # Haiku and Fable resolve natively in the original profile.
            self.assertNotIn('ANTHROPIC_DEFAULT_HAIKU_MODEL', installed['env'])
            for model in ('opus', 'sonnet', 'haiku', 'fable', 'claude-haiku-5-5', 'claude-fable-5-1'):
                self.assertIn(model, installed['availableModels'])
            self.assertIn('claude-sonnet-5', installed['availableModels'])
            self.assertNotIn('nvidia/nemotron-3.5-lightning:free', installed['availableModels'])
            self.assertEqual(installed['model'], 'fable')
            self.assertNotIn('ANTHROPIC_BASE_URL', installed['env'])
            self.assertNotIn('hooks', installed)
            self.assertNotIn('statusLine', installed)
            self.assertEqual(installed['permissions']['additionalDirectories'], ['example-directory'])
            self.assertEqual(unrelated.read_text(), 'unrelated custom skill')
            self.assertIn('Existing user instructions.', instructions.read_text())
            # Nothing for the removed router profile or its launcher.
            self.assertFalse((home / '.claude/profiles').exists())
            self.assertFalse((home / '.claude/launcher/bin').exists())
            self.assertFalse((home / '.claude/launcher/models.json').exists())
            self.assertEqual(sorted(p.name for p in (home / '.claude/launcher/runtime').iterdir()), ['core.py', 'rollback.py'])
            # The block markers keep their historical name so existing installs are found and replaced.
            rules = (home / '.claude/CLAUDE.md').read_text(encoding='utf-8').replace('claude-openrouter-kit', 'kit-block')
            self.assertNotIn('router', rules.casefold())
            self.assertTrue(all(Path(row['backup']).is_file() for row in instance.state['files'] if row.get('backup')))
            repeat = install.Installer(home)
            repeat.install(native, update_path=False)
            repeated = install.load(original)
            self.assertEqual(repeated, installed)
            self.assertEqual(instructions.read_text().count('<!-- claude-openrouter-kit:start -->'), 1)
            self.assertEqual(unrelated.read_text(), 'unrelated custom skill')
            with patch.object(rollback, 'KIT', repeat.kit):
                rollback.rollback()
            self.assertEqual(unrelated.read_text(), 'unrelated custom skill')
            (instance.kit / 'installation.json').write_text(json.dumps(initial_state))
            with patch.object(rollback, 'KIT', instance.kit):
                rollback.rollback()
            self.assertEqual(install.load(original)['theme'], 'light')
            self.assertEqual(install.load(original)['env']['ANTHROPIC_DEFAULT_FABLE_MODEL'], 'claude-opus-5-5')
            self.assertEqual(instructions.read_text(), 'Existing user instructions.')
            self.assertEqual(unrelated.read_text(), 'unrelated custom skill')

    def test_reinstall_drops_launcher_hooks_and_keeps_user_hooks(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            original = home / '.claude/settings.json'
            original.parent.mkdir()
            user_hook = {'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': 'my-own-check'}]}
            events = ('UserPromptSubmit', 'SessionStart', 'PreToolUse', 'PostToolUse', 'PostToolUseFailure', 'SubagentStart', 'SubagentStop', 'Stop')
            hooks = {event: [legacy_hook(home)] for event in events}
            hooks['StopFailure'] = [legacy_hook(home, 'rate_limit')]
            hooks['PreToolUse'].insert(0, user_hook)
            original.write_text(json.dumps({'model': 'opus', 'hooks': hooks}))
            before = original.read_bytes()
            native = fixture_native(home)
            instance = install.Installer(home)
            instance.install(native, update_path=False)
            installed = install.load(original)
            self.assertEqual(installed['hooks'], {'PreToolUse': [user_hook]})
            # The settings change is journaled, so the installer's rollback brings the old rows back.
            with patch.object(rollback, 'KIT', instance.kit):
                rollback.rollback()
            self.assertEqual(original.read_bytes(), before)

    def test_path_puts_native_first_and_drops_launcher_bin(self):
        native_dir = r'D:\Home\.local\bin'
        legacy = r'D:\Home\.claude\launcher\bin'
        # Windows compares PATH entries without case; other systems keep case.
        duplicate = native_dir.upper() if os.name == 'nt' else native_dir
        before = legacy + ';C:\\Tools;' + duplicate + '\\;C:\\Other'
        result = install.path_entries(before, native_dir, legacy)
        self.assertEqual(result, native_dir + ';C:\\Tools;C:\\Other')
        self.assertEqual(install.path_entries(result, native_dir, legacy), result)

    def test_original_model_defaults_and_custom_haiku_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            original = home / '.claude/settings.json'
            original.parent.mkdir()
            native = fixture_native(home)
            # Absent model -> Opus; a non-Anthropic ID is reset; a user's own Haiku pin is kept.
            for before, expected in ((None, 'opus'), ('nvidia/nemotron-3.5-lightning:free', 'opus'), ('claude-opus-5-5[1m]', 'claude-opus-5-5[1m]'), ('sonnet', 'sonnet')):
                data = {'env': {'ANTHROPIC_DEFAULT_HAIKU_MODEL': 'claude-haiku-5-5'}}
                if before:
                    data['model'] = before
                original.write_text(json.dumps(data))
                install.Installer(home).install(native, update_path=False)
                installed = install.load(original)
                self.assertEqual(installed['model'], expected)
                self.assertEqual(installed['env']['ANTHROPIC_DEFAULT_HAIKU_MODEL'], 'claude-haiku-5-5')
                self.assertEqual(installed['availableModels'][:8], install.ORIGINAL_MODELS)

    def test_external_link_refused(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as external:
            home = Path(temp)
            instance = install.Installer(home)
            with self.assertRaises(RuntimeError):
                instance.checked(Path(external) / 'settings.json')

    def test_rollback_restores_original_and_refuses_new_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); original = root / 'settings.json'; saved = root / 'saved.bak'
            original.write_text('installed', encoding='utf-8'); saved.write_text('original', encoding='utf-8')
            state = {'files': [{'path': str(original), 'backup': str(saved), 'installed': core.file_hash(original)}],
                     'created': [], 'path_before': None}
            core.atomic_json(root / 'installation.json', state)
            with patch.object(rollback, 'KIT', root):
                original.write_text('new user edit', encoding='utf-8')
                with self.assertRaises(RuntimeError):
                    rollback.rollback()
                self.assertEqual(original.read_text(), 'new user edit')
                original.write_text('installed', encoding='utf-8')
                rollback.rollback()
                self.assertEqual(original.read_text(), 'original')

    def test_templates_have_no_router_policy(self):
        for name in ('CLAUDE.md', 'GEMINI.md'):
            text = (ROOT / 'templates' / name).read_text(encoding='utf-8').casefold()
            for word in ('router', 'openrouter', 'omniroute', 'handoff'):
                self.assertNotIn(word, text, name)
        claude = (ROOT / 'templates/CLAUDE.md').read_text(encoding='utf-8')
        for model in ('`haiku`', '`sonnet`', '`opus`', '`fable`'):
            self.assertIn(model, claude)

if __name__ == '__main__':
    unittest.main()
