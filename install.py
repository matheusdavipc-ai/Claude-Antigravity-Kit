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
from core import MODEL_NAMES, PICKER, ROLES, protect_directory, router_env
from context_config import context_plan, context_settings, context_picker, native_model

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

def hook_config(python, kit, events):
    # command + args is supported by the targeted Claude Code release.
    return {event: [{'matcher': matcher, 'hooks': [{'type': 'command', 'command': str(python), 'args': [str(kit / 'runtime/hook.py')], 'timeout': 15}]}] for event, matcher in events.items()}

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
        for relative, kind in (('.claude/skills', 'skills'), ('.claude/agents', 'agents'), ('.claude/commands', 'global_workflows'), ('.claude/profiles/router/skills', 'skills')):
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
        protect_directory(self.kit / 'runs')
        if (self.kit / 'installation.json').is_file():
            shutil.copy2(self.kit / 'installation.json', self.backup / 'previous-installation.json')
        self.journal()
        self.write(self.kit / 'models.json', (ROOT / 'models.json').read_bytes())
        for file in (file for file in (ROOT / 'runtime').iterdir() if file.suffix in ('.py','.mjs')):
            self.write(self.kit / 'runtime' / file.name, file.read_bytes())
        self.write(self.kit / 'config.json', {'native_executable': str(native), 'python': sys.executable})
        self.assets()
        original_path = self.home / '.claude/settings.json'
        original = load(original_path)
        env = original.setdefault('env', {})
        for key in ('ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL'):
            env.pop(key, None)
        env.update({'ANTHROPIC_DEFAULT_OPUS_MODEL': 'claude-opus-5-5', 'ANTHROPIC_DEFAULT_SONNET_MODEL': 'claude-sonnet-5-5', 'ANTHROPIC_DEFAULT_HAIKU_MODEL': 'claude-sonnet-5-5', 'ANTHROPIC_DEFAULT_FABLE_MODEL': 'claude-opus-5-5'})
        original.setdefault('model', 'sonnet')
        if str(original['model']).removesuffix('[1m]') not in ('sonnet','opus','opusplan','claude-sonnet-5-5','claude-opus-5-5'):
            original['model'] = 'sonnet'
        original['availableModels'] = ['sonnet', 'opus', 'claude-sonnet-5-5', 'claude-opus-5-5']
        original.setdefault('permissions', {'defaultMode': 'default'})
        events = {'UserPromptSubmit': '', 'SessionStart': '', 'PreToolUse': '', 'PostToolUse': '', 'PostToolUseFailure': '', 'SubagentStart': '', 'SubagentStop': '', 'Stop': '', 'StopFailure': 'rate_limit'}
        hooks = original.setdefault('hooks', {})
        for event, rows in hook_config(sys.executable, self.kit, events).items():
            previous = hooks.get(event, [])
            previous = [row for row in previous if not any(str(self.kit / 'runtime/hook.py') in hook.get('args', []) for hook in row.get('hooks', []))]
            hooks[event] = previous + rows
        self.write(original_path, original)
        router = self.home / '.claude/profiles/router'
        protect_directory(router / 'secrets')
        settings = load(router / 'settings.json')
        settings.setdefault('permissions', {'defaultMode': 'default'})
        settings['model'] = native_model(ROLES['router-orchestrator'][0])
        settings['availableModels'] = list(MODEL_NAMES) + [native_model(model) for model in MODEL_NAMES if native_model(model) != model]
        settings['modelPicker'] = context_picker(PICKER)
        settings['modelSettings'] = context_settings()
        settings.setdefault('env', {}).update(router_env())
        for key in ('ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_BASE_URL'):
            settings['env'].pop(key, None)
        settings.setdefault('hooks', {})['PreToolUse'] = hook_config(sys.executable, self.kit, {'PreToolUse': 'Agent'})['PreToolUse']
        self.write(router / 'settings.json', settings)
        self.write(router / 'upstream.json', {**load(router / 'upstream.json'), 'url': 'http://127.0.0.1:20128', 'transport': 'omniroute'})
        for template, path in (('CLAUDE.md', self.home / '.claude/CLAUDE.md'), ('GEMINI.md', self.home / '.gemini/GEMINI.md')):
            existing = path.read_text(encoding='utf-8') if path.is_file() else ''
            addition = (ROOT / 'templates' / template).read_text(encoding='utf-8')
            self.write(path, managed_block(existing, addition))
        self.write(router / 'CLAUDE.md', (ROOT / 'templates/ROUTER.md').read_bytes())
        for agent in (ROOT / 'templates/router-agents').glob('*.md'):
            text = agent.read_text(encoding='utf-8')
            base = ROLES[agent.stem][0]
            text = re.sub(r'^model: .+$', 'model: ' + native_model(base), text, count=1, flags=re.M)
            self.write(router / 'agents' / agent.name, text)
        self.write(self.kit / 'README.md', (ROOT / 'README.md').read_bytes())
        self.write(self.kit / 'models.json', (ROOT / 'models.json').read_bytes())
        bindir = self.kit / 'bin'
        for command, profile in (('claude', 'original'), ('clauderouter', 'router')):
            if os.name == 'nt':
                self.write(bindir / (command + '.cmd'), f'@echo off\r\n"{sys.executable}" "{self.kit / "runtime/launcher.py"}" {profile} %*\r\n')
            else:
                target = bindir / command
                self.write(target, '#!/bin/sh\nexec ' + shlex.quote(sys.executable) + ' ' + shlex.quote(str(self.kit / 'runtime/launcher.py')) + ' ' + profile + ' "$@"\n')
                target.chmod(0o755)
        if update_path:
            self.install_path(bindir)
        self.state['complete'] = True
        self.journal()

    def install_path(self, bindir):
        if os.name == 'nt':
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as registry:
                try:
                    before, kind = winreg.QueryValueEx(registry, 'Path')
                except FileNotFoundError:
                    before, kind = '', winreg.REG_EXPAND_SZ
                installed = ';'.join([str(bindir)] + [p for p in before.split(';') if p and p.casefold() != str(bindir).casefold()])
                self.state.update(path_before=before, path_installed=installed)
                self.journal()
                winreg.SetValueEx(registry, 'Path', 0, kind, installed)
            import ctypes
            ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x1A, 0, 'Environment', 2, 2000, None)
        else:
            path = self.home / '.zshrc'
            existing = path.read_text(encoding='utf-8') if path.is_file() else ''
            begin, end = '# claude-openrouter-kit:start', '# claude-openrouter-kit:end'
            block = begin + '\nexport PATH=' + shlex.quote(str(bindir)) + ':"$PATH"\n' + end
            if begin in existing:
                result = re.sub(re.escape(begin) + r'.*?' + re.escape(end), lambda m: block, existing, flags=re.S)
            else:
                result = existing.rstrip() + '\n\n' + block + '\n'
            self.write(path, result)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true', help='Show the installation plan without writing files')
    parser.add_argument('--skip-key', action='store_true', help='Defer local OmniRoute pool setup')
    parser.add_argument('--no-path', action='store_true')
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--native-executable', type=Path)
    parser.add_argument('--skip-prerequisites', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.dry_run:
        print(json.dumps({'home': str(args.home), 'profiles': ['.claude', '.claude/profiles/router'], 'runtime': '.claude/launcher', 'shared_kit': '.gemini/config', 'models': MODEL_NAMES, 'roles': ROLES, 'dry_run': True}, ensure_ascii=False, indent=2))
        return 0
    if sys.version_info < (3, 12):
        raise RuntimeError('Python 3.12 ou superior necessario.')
    if os.name != 'nt' and sys.platform != 'darwin' and not args.skip_prerequisites:
        raise RuntimeError('Instalacao suportada em Windows e macOS.')
    # Keep the native installer's stable symlink on macOS so auto-updates keep working.
    native = (args.native_executable or args.home / '.local/bin' / ('claude.exe' if os.name == 'nt' else 'claude')).absolute()
    if not args.skip_prerequisites:
        if not native.is_file() or native.parent == (args.home / '.claude/launcher/bin').resolve():
            raise RuntimeError('Instale o Claude Code NATIVO pelo instalador oficial antes de continuar.')
        result = subprocess.run([str(native), '--version'], capture_output=True, text=True, timeout=20, check=True)
        match = re.search(r'(\d+)\.(\d+)\.(\d+)', result.stdout)
        if not match or tuple(map(int, match.groups())) < (2, 1, 292):
            raise RuntimeError('Claude Code 2.1.292 ou superior necessario.')
    instance = Installer(args.home)
    instance.install(native, update_path=not args.no_path)
    print('Kit global instalado. Reabra o terminal; o clone pode ser movido sem quebrar a instalacao.')
    print('Login da assinatura: execute o Claude nativo e /login. Nao copie credenciais de outro computador.')
    if not args.skip_key:
        env = dict(os.environ, CLAUDE_KIT_HOME=str(args.home.resolve()))
        result = subprocess.run([sys.executable, str(instance.kit / 'runtime/omniroute_pool.py')], env=env)
        if result.returncode:
            print('Arquivos instalados; chave ainda pendente. Execute runtime/omniroute_pool.py no diretorio instalado.', file=sys.stderr)
            return result.returncode
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print('Instalacao interrompida: ' + str(error), file=sys.stderr)
        print('Alteracoes parciais possuem registro protegido em ~/.claude/launcher/installation.json.', file=sys.stderr)
        sys.exit(1)
