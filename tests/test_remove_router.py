import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import remove_router as rr


def tree(root):
    """Relative path -> sha256 (files) or 'link:<target>' (links), never following links."""
    result = {}
    for folder, dirs, files in os.walk(root):
        for name in dirs + files:
            path = Path(folder) / name
            relative = path.relative_to(root).as_posix()
            if rr.is_link(path):
                result[relative] = 'link:' + os.path.normcase(os.path.realpath(path))
            elif path.is_file():
                result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        dirs[:] = [d for d in dirs if not rr.is_link(Path(folder) / d)]
    return result


def write(path, text='fixture'):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


class RemoveRouterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name).resolve()
        h = self.home
        write(h / '.claude/settings.json', json.dumps({'model': 'opus', 'hooks': {'PreToolUse': [{'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': 'my-own-check'}]}]}}))
        write(h / '.claude/CLAUDE.md', 'user rules')
        write(h / '.gemini/config/skills/a/SKILL.md', 'shared skill')
        write(h / '.omniroute/.env', 'SYNTHETIC=1')
        launcher = h / '.claude/launcher'
        for name in ('core.py', 'rollback.py', 'hook.py', 'launcher.py', 'quota_watch.py', 'gateway.py', 'omniroute_pool.py'):
            write(launcher / 'runtime' / name)
        write(launcher / 'runtime/__pycache__/core.cpython-314.pyc')
        write(launcher / 'bin/claude.cmd')
        write(launcher / 'bin/clauderouter.cmd')
        write(launcher / 'models.json', '{}')
        write(launcher / 'config.json', '{}')
        write(launcher / 'installation.json', '{}')
        write(launcher / '03-trocar-chave.cmd')
        write(launcher / '04-limpar-caminhos-antigos.cmd')
        write(launcher / 'runs/r1/router-session.json', '{"env":{}}')
        write(launcher / 'runs/r1/1.event.json', '{}')
        write(launcher / 'backups/old/0.bak')
        write(launcher / 'historico/perfil-router-anterior/settings.json', '{}')
        write(h / '.claude/profiles/router/settings.json', '{}')
        write(h / '.claude/profiles/router/secrets/omniroute.dpapi', 'encrypted fixture')
        for link in (h / '.claude/profiles/router/skills', launcher / 'historico/perfil-router-anterior/skills'):
            rr.create_link(link, h / '.gemini/config/skills')
        self.before = tree(h)

    def tearDown(self):
        self.temp.cleanup()

    def test_dry_run_lists_router_first_launcher_last_and_changes_nothing(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            rows = rr.report(self.home, [], '')
        phases = [phase for phase, _ in rows]
        self.assertEqual(phases, sorted(phases, key=lambda p: p != 'router'))
        names = [path.name for _, path in rows]
        for expected in ('clauderouter.cmd', 'router', 'gateway.py', 'omniroute_pool.py', 'models.json', '03-trocar-chave.cmd',
                         'perfil-router-anterior', 'router-session.json', 'hook.py', 'launcher.py', 'quota_watch.py', 'claude.cmd', 'config.json'):
            self.assertIn(expected, names)
        for kept in ('core.py', 'rollback.py', '04-limpar-caminhos-antigos.cmd', 'installation.json', '1.event.json'):
            self.assertNotIn(kept, names)
        self.assertIn('Bloqueios para --aplicar agora: nenhum', output.getvalue())
        self.assertEqual(tree(self.home), self.before)

    def test_apply_quarantines_and_restore_brings_everything_back(self):
        journal_path = rr.apply(self.home, [], '', stamp='test')
        after = tree(self.home)
        launcher = '.claude/launcher/'
        # Original profile, shared kit, OmniRoute data, logs and backups stay where they were.
        for kept in ('.claude/settings.json', '.claude/CLAUDE.md', '.gemini/config/skills/a/SKILL.md', '.omniroute/.env',
                     launcher + 'runtime/core.py', launcher + 'runtime/rollback.py', launcher + 'installation.json',
                     launcher + 'runs/r1/1.event.json', launcher + 'backups/old/0.bak', launcher + '04-limpar-caminhos-antigos.cmd'):
            self.assertEqual(after[kept], self.before[kept], kept)
        for gone in ('.claude/profiles', launcher + 'bin', launcher + 'runtime/hook.py', launcher + 'runtime/__pycache__',
                     launcher + 'runs/r1/router-session.json', launcher + 'historico/perfil-router-anterior', launcher + 'models.json'):
            self.assertFalse((self.home / gone).exists(), gone)
        quarantine = self.home / '.claude/launcher/backups/remocao-router-test/quarentena'
        self.assertEqual((quarantine / '.claude/profiles/router/secrets/omniroute.dpapi').read_text(), 'encrypted fixture')
        # Links were removed as links: the shared skills folder is intact and nothing in quarantine points to it.
        self.assertFalse((quarantine / '.claude/profiles/router/skills').exists())
        journal = json.loads(journal_path.read_text(encoding='utf-8'))
        self.assertTrue(journal['complete'])
        self.assertTrue(all(entry['done'] for entry in journal['entries']))
        self.assertEqual([e['phase'] for e in journal['entries']], sorted((e['phase'] for e in journal['entries']), key=lambda p: p != 'router'))
        rr.restore(journal_path)
        restored = tree(self.home)
        for path, value in self.before.items():
            self.assertEqual(restored.get(path), value, path)

    def test_refuses_while_settings_still_call_the_launcher(self):
        settings = self.home / '.claude/settings.json'
        script = str(self.home / '.claude/launcher/runtime/hook.py')
        settings.write_text(json.dumps({'hooks': {'Stop': [{'matcher': '', 'hooks': [{'type': 'command', 'command': 'python', 'args': [script]}]}]}}))
        before = tree(self.home)
        with self.assertRaises(RuntimeError) as raised:
            rr.apply(self.home, [], '', stamp='test')
        self.assertIn('settings.json', str(raised.exception))
        self.assertEqual(tree(self.home), before)

    def test_refuses_with_open_sessions_unknown_processes_or_old_path(self):
        bin_dir = str(self.home / '.claude/launcher/bin')
        for sessions, path_value, message in (([ '123 python.exe'], '', 'Sessoes'), (None, '', 'processos'),
                                              ([], bin_dir + os.pathsep + 'other', 'PATH')):
            with self.assertRaises(RuntimeError) as raised:
                rr.apply(self.home, sessions, path_value, stamp='test')
            self.assertIn(message, str(raised.exception))
            self.assertEqual(tree(self.home), self.before)

    def test_restore_refuses_to_overwrite(self):
        journal_path = rr.apply(self.home, [], '', stamp='test')
        write(self.home / '.claude/launcher/models.json', 'new file created later')
        with self.assertRaises(RuntimeError):
            rr.restore(journal_path)
        self.assertEqual((self.home / '.claude/launcher/models.json').read_text(), 'new file created later')


if __name__ == '__main__':
    unittest.main()
