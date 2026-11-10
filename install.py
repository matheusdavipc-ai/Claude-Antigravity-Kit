"""Install the kit globally, preserving unrelated files and journaling every change."""
import argparse
import datetime
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'runtime'))
from core import protect_directory

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.is_file() else {}

def managed_block(existing, addition):
    begin, end = '<!-- claude-openrouter-kit:start -->', '<!-- claude-openrouter-kit:end -->'
    block = begin + '\n' + addition.rstrip() + '\n' + end
    pattern = re.escape(begin) + r'.*?' + re.escape(end)
    if re.search(pattern, existing, re.S):
        return re.sub(pattern, lambda match: block, existing, flags=re.S)
    return existing.rstrip() + ('\n\n' if existing.strip() else '') + block + '\n'

ORIGINAL_MODELS = ['opus', 'sonnet', 'haiku', 'fable', 'claude-opus-5-5', 'claude-sonnet-5-5', 'claude-haiku-5-5', 'claude-fable-5-1']
ORIGINAL_ALIASES = {'opus', 'sonnet', 'haiku', 'fable', 'opusplan', 'best', 'default'}
LEGACY_HAIKU_REMAP = 'claude-sonnet-5-5'

def original_model_valid(model):
    # Anthropic aliases and claude-* IDs only; IDs from other providers never reach the profile.
    if not isinstance(model, str) or not model:
        return False
    base = model.removesuffix('[1m]')
    return base in ORIGINAL_ALIASES or bool(re.fullmatch(r'claude-[a-z0-9.-]+', base))

def same_path(first, second):
    return os.path.normcase(os.path.normpath(str(first))).rstrip('\\/') == os.path.normcase(os.path.normpath(str(second))).rstrip('\\/')

def drop_kit_hooks(settings, script):
    # Earlier versions registered launcher/runtime/hook.py for the subscription supervisor.
    # Remove only those rows; hooks written by the user or other tools stay untouched.
    hooks = settings.get('hooks')
    if not isinstance(hooks, dict):
        return settings
    def ours(row):
        for hook in row.get('hooks', []) if isinstance(row, dict) else []:
            values = [hook.get('command', '')] + list(hook.get('args', []) or [])
            if any(isinstance(value, str) and same_path(value.strip('"'), script) for value in values):
                return True
            if isinstance(hook.get('command'), str) and os.path.normcase(str(script)) in os.path.normcase(hook['command']):
                return True
        return False
    for event in list(hooks):
        rows = hooks[event]
        if not isinstance(rows, list):
            continue
        kept = [row for row in rows if not ours(row)]
        if kept:
            hooks[event] = kept
        else:
            hooks.pop(event)
    if not hooks:
        settings.pop('hooks')
    return settings

def path_entries(before, native_dir, legacy_dir):
    # Native Claude first; the old launcher wrapper directory leaves the PATH.
    rest = [p for p in before.split(';') if p and not same_path(p, native_dir) and not same_path(p, legacy_dir)]
    return ';'.join([str(native_dir)] + rest)

class Installer:
    def __init__(self, home):
        self.home = home.resolve()
        self.kit = self.home / '.claude/launcher'
        self.backup = self.kit / 'backups' / ('install-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
        self.state = {'complete': False, 'files': [], 'created': [], 'path_before': None, 'backup': str(self.backup)}

    def checked(self, path):
        path = Path(path)
        if not path.resolve().is_relative_to(self.home):
            raise RuntimeError('Destino fora do usuario; operacao recusada: ' + str(path))
        return path

    def journal(self):
        target = self.kit / 'installation.json'
        temporary = target.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temporary, target)

    def write(self, path, data):
        path = self.checked(path)
        if isinstance(data, (dict, list)):
            data = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
        if isinstance(data, str):
            data = data.encode('utf-8')
        if path.is_file() and path.read_bytes() == data:
            return
        entry = {'path': str(path), 'planned': hashlib.sha256(data).hexdigest()}
        if path.exists():
            if not path.is_file() or path.is_symlink():
                raise RuntimeError('Arquivo de destino inesperado; preservado: ' + str(path))
            saved = self.backup / (str(len(self.state['files'])) + '.bak')
            shutil.copy2(path, saved)
            entry.update(backup=str(saved), before=digest(saved))
        else:
            self.state['created'].append(str(path))
        self.state['files'].append(entry)
        self.journal()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + '.kit-tmp')
        temporary.write_bytes(data)
        os.replace(temporary, path)
        entry['installed'] = digest(path)
        self.journal()

    def assets(self):
        for kind in ('skills', 'agents', 'global_workflows'):
            for source in sorted((ROOT / 'bundle' / kind).rglob('*')):
                if source.is_file():
                    self.write(self.home / '.gemini/config' / kind / source.relative_to(ROOT / 'bundle' / kind), source.read_bytes())
        # Merge individual assets into existing real directories, or link absent ones.
        for relative, kind in (('.claude/skills', 'skills'), ('.claude/agents', 'agents'), ('.claude/commands', 'global_workflows')):
            destination = self.home / relative
            source = self.home / '.gemini/config' / kind
            if destination.is_symlink() or (hasattr(destination, 'is_junction') and destination.is_junction()):
                if destination.resolve() != source.resolve():
                    raise RuntimeError('Link existente aponta para outro kit; preservado: ' + str(destination))
            elif destination.exists():
                if not destination.is_dir():
                    raise RuntimeError('Destino de skills/agentes inesperado.')
                for asset in sorted((ROOT / 'bundle' / kind).rglob('*')):
                    if asset.is_file():
                        self.write(destination / asset.relative_to(ROOT / 'bundle' / kind), asset.read_bytes())
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                self.state.setdefault('created_links', []).append({'path': str(destination), 'target': str(source)})
                self.journal()
                if os.name == 'nt':
                    script = "New-Item -ItemType Junction -Path '" + str(destination).replace("'", "''") + "' -Target '" + str(source).replace("'", "''") + "' | Out-Null"
                    subprocess.run(['powershell.exe', '-NoProfile', '-Command', script], check=True, capture_output=True)
                else:
                    destination.symlink_to(source, target_is_directory=True)

    def install(self, native, update_path=True):
        protect_directory(self.backup)
        if (self.kit / 'installation.json').is_file():
            shutil.copy2(self.kit / 'installation.json', self.backup / 'previous-installation.json')
        self.journal()
        for name in ('core.py', 'rollback.py'):
            self.write(self.kit / 'runtime' / name, (ROOT / 'runtime' / name).read_bytes())
        self.assets()
        original_path = self.home / '.claude/settings.json'
        original = load(original_path)
        env = original.setdefault('env', {})
        for key in ('ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL'):
            env.pop(key, None)
        env.update({'ANTHROPIC_DEFAULT_OPUS_MODEL': 'claude-opus-5-5', 'ANTHROPIC_DEFAULT_SONNET_MODEL': 'claude-sonnet-5-5'})
        # Haiku resolves natively. Drop only the remap written by earlier kit versions.
        if env.get('ANTHROPIC_DEFAULT_HAIKU_MODEL') == LEGACY_HAIKU_REMAP:
            env.pop('ANTHROPIC_DEFAULT_HAIKU_MODEL')
        # A Fable override equal to Opus makes native billing classify Opus as Fable.
        # The profile uses native Fable resolution: never write a Fable override.
        for key in list(env):
            if key.startswith('ANTHROPIC_DEFAULT_FABLE_MODEL'):
                env.pop(key)
        # Preserve the user's model; reset only values that cannot reach Anthropic.
        if not original_model_valid(original.get('model')):
            original['model'] = 'opus'
        existing = [model for model in original.get('availableModels', []) if original_model_valid(model)]
        original['availableModels'] = ORIGINAL_MODELS + [model for model in existing if model not in ORIGINAL_MODELS]
        original.setdefault('permissions', {'defaultMode': 'default'})
        drop_kit_hooks(original, self.kit / 'runtime/hook.py')
        self.write(original_path, original)
        for template, path in (('CLAUDE.md', self.home / '.claude/CLAUDE.md'), ('GEMINI.md', self.home / '.gemini/GEMINI.md')):
            existing = path.read_text(encoding='utf-8') if path.is_file() else ''
            addition = (ROOT / 'templates' / template).read_text(encoding='utf-8')
            self.write(path, managed_block(existing, addition))
        self.write(self.kit / 'README.md', (ROOT / 'README.md').read_bytes())
        if update_path:
            self.install_path(Path(native).parent)
        self.state['complete'] = True
        self.journal()

    def install_path(self, native_dir):
        legacy = self.kit / 'bin'
        if os.name == 'nt':
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as registry:
                try:
                    before, kind = winreg.QueryValueEx(registry, 'Path')
                except FileNotFoundError:
                    before, kind = '', winreg.REG_EXPAND_SZ
                installed = path_entries(before, native_dir, legacy)
                if installed == before:
                    return
                self.state.update(path_before=before, path_installed=installed)
                self.journal()
                winreg.SetValueEx(registry, 'Path', 0, kind, installed)
            import ctypes
            ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x1A, 0, 'Environment', 2, 2000, None)
        else:
            path = self.home / '.zshrc'
            existing = path.read_text(encoding='utf-8') if path.is_file() else ''
            begin, end = '# claude-openrouter-kit:start', '# claude-openrouter-kit:end'
            block = begin + '\nexport PATH=' + shlex.quote(str(native_dir)) + ':"$PATH"\n' + end
            if begin in existing:
                result = re.sub(re.escape(begin) + r'.*?' + re.escape(end), lambda m: block, existing, flags=re.S)
            else:
                result = existing.rstrip() + '\n\n' + block + '\n'
            self.write(path, result)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true', help='Show the installation plan without writing files')
    parser.add_argument('--no-path', action='store_true')
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--native-executable', type=Path)
    parser.add_argument('--skip-prerequisites', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    # Keep the native installer's stable symlink on macOS so auto-updates keep working.
    native = (args.native_executable or args.home / '.local/bin' / ('claude.exe' if os.name == 'nt' else 'claude')).absolute()
    if args.dry_run:
        print(json.dumps({'home': str(args.home), 'profile': '.claude', 'runtime': '.claude/launcher', 'shared_kit': '.gemini/config',
                          'claude': str(native), 'path_first': str(native.parent), 'dry_run': True}, ensure_ascii=False, indent=2))
        return 0
    if sys.version_info < (3, 12):
        raise RuntimeError('Python 3.12 ou superior necessario.')
    if os.name != 'nt' and sys.platform != 'darwin' and not args.skip_prerequisites:
        raise RuntimeError('Instalacao suportada em Windows e macOS.')
    if not args.skip_prerequisites:
        if not native.is_file() or native.parent == (args.home / '.claude/launcher/bin').resolve():
            raise RuntimeError('Instale o Claude Code NATIVO pelo instalador oficial antes de continuar.')
        result = subprocess.run([str(native), '--version'], capture_output=True, text=True, timeout=20, check=True)
        match = re.search(r'(\d+)\.(\d+)\.(\d+)', result.stdout)
        if not match or tuple(map(int, match.groups())) < (2, 1, 292):
            raise RuntimeError('Claude Code 2.1.292 ou superior necessario.')
    instance = Installer(args.home)
    instance.install(native, update_path=not args.no_path)
    print('Kit global instalado. Reabra o terminal; o comando claude abre o Claude Code nativo.')
    print('Login da assinatura: execute claude e /login. Nao copie credenciais de outro computador.')
    print('Instalacao anterior com o perfil router? Veja scripts/remove_router.py --dry-run.')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print('Instalacao interrompida: ' + str(error), file=sys.stderr)
        print('Alteracoes parciais possuem registro protegido em ~/.claude/launcher/installation.json.', file=sys.stderr)
        sys.exit(1)
