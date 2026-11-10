"""Move what earlier kit versions installed for the router profile into a journaled quarantine.

    python scripts/remove_router.py --dry-run      lists items and checks, changes nothing
    python scripts/remove_router.py --aplicar      moves items, router files first, launcher last
    python scripts/remove_router.py --restaurar JOURNAL   moves everything back

Run --aplicar outside Claude Code, with every claude/clauderouter session closed, after the
current installer has removed the launcher hooks and PATH entry. Nothing is deleted: items are
moved to ~/.claude/launcher/backups/remocao-router-<time>/quarentena. Links are removed as links,
never followed. ~/.omniroute, OpenRouter keys and the original profile are never touched.
"""
import argparse
import base64
import datetime
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

ROUTER_RUNTIME = ('gateway.py', 'router_gate.py', 'agent_guard.py', 'omniroute_pool.py', 'omniroute_bridge.mjs',
                  'replace_key.py', 'context_config.py', 'test_profiles.py', 'verify_install.py', 'cleanup_legacy_paths.py')
LAUNCHER_RUNTIME = ('hook.py', 'launcher.py', 'quota_watch.py', '__pycache__')
NEVER = ('.omniroute',)


def is_link(path):
    path = Path(path)
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return False
    return path.is_symlink() or bool(getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))


def link_target(path):
    return os.path.realpath(path)


def plan(home):
    """Ordered (phase, path) pairs that exist. Router items first; the launcher wrapper last."""
    claude = home / '.claude'
    launcher = claude / 'launcher'
    items = [('router', launcher / 'bin' / name) for name in ('clauderouter.cmd', 'clauderouter')]
    items.append(('router', claude / 'profiles/router'))
    items += [('router', launcher / 'runtime' / name) for name in ROUTER_RUNTIME]
    items += [('router', launcher / 'models.json'), ('router', launcher / '03-trocar-chave.cmd'),
              ('router', launcher / 'historico/perfil-router-anterior')]
    runs = launcher / 'runs'
    if runs.is_dir() and not is_link(runs):
        items += [('router', session) for session in sorted(runs.glob('*/router-session.json'))]
    items += [('final', launcher / 'runtime' / name) for name in LAUNCHER_RUNTIME]
    items += [('final', launcher / 'bin' / name) for name in ('claude.cmd', 'claude')]
    items.append(('final', launcher / 'config.json'))
    return [(phase, path) for phase, path in items if path.exists() or is_link(path)]


def empty_dirs(home):
    # Removed only when nothing else is left inside them.
    return [home / '.claude/launcher/bin', home / '.claude/profiles']


def size(path):
    if is_link(path) or path.is_file():
        return 0 if is_link(path) else path.stat().st_size
    total = 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not is_link(Path(root) / d)]
        total += sum((Path(root) / f).stat().st_size for f in files if not is_link(Path(root) / f))
    return total


def file_hashes(path):
    if path.is_file() and not is_link(path):
        return {'.': hashlib.sha256(path.read_bytes()).hexdigest()}
    result = {}
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not is_link(Path(root) / d)]
        for name in files:
            file = Path(root) / name
            if not is_link(file):
                result[file.relative_to(path).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
    return result


def inner_links(path):
    found = []
    for root, dirs, files in os.walk(path):
        for name in dirs + files:
            candidate = Path(root) / name
            if is_link(candidate):
                found.append(candidate)
        dirs[:] = [d for d in dirs if not is_link(Path(root) / d)]
    return found


def remove_link(path):
    # rmdir/unlink act on the link itself; the target folder is never entered.
    if path.is_dir():
        os.rmdir(path)
    else:
        os.unlink(path)


def create_link(path, target):
    if os.name == 'nt':
        import _winapi
        _winapi.CreateJunction(str(target), str(path))
    else:
        os.symlink(target, path, target_is_directory=True)


def running_sessions():
    """'pid name' of processes that still use the launcher or the router; None if unknown."""
    markers = ('.claude/launcher/runtime', '.claude/launcher/runs', '.claude/launcher/bin', 'clauderouter', '.claude/profiles/router')
    try:
        if os.name == 'nt':
            script = "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine } | ForEach-Object { [string]$_.ProcessId + ' ' + $_.Name + ' ' + $_.CommandLine }"
            result = subprocess.run(['powershell.exe', '-NoProfile', '-EncodedCommand', base64.b64encode(script.encode('utf-16-le')).decode()],
                                    capture_output=True, timeout=60)
            if result.returncode:
                return None
            lines = result.stdout.decode('utf-8', 'replace').splitlines()
        else:
            result = subprocess.run(['ps', '-axo', 'pid=,comm=,command='], capture_output=True, text=True, timeout=30)
            if result.returncode:
                return None
            lines = result.stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        return None
    hits = []
    for line in lines:
        parts = line.strip().split(None, 2)
        if len(parts) < 3 or parts[0] == str(os.getpid()):
            continue
        command = parts[2].replace('\\', '/').casefold()
        if any(marker in command for marker in markers):
            # Only the id and executable name are reported; arguments may contain private paths.
            hits.append(parts[0] + ' ' + Path(parts[1]).name)
    return hits


def user_path(home):
    if os.name == 'nt':
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment') as registry:
            try:
                return winreg.QueryValueEx(registry, 'Path')[0]
            except FileNotFoundError:
                return ''
    zshrc = home / '.zshrc'
    return zshrc.read_text(encoding='utf-8') if zshrc.is_file() else ''


def checks(home, sessions, path_value):
    """Reasons that block --aplicar. Empty list means it is safe to proceed."""
    problems = []
    launcher = home / '.claude/launcher'
    settings_path = home / '.claude/settings.json'
    try:
        settings = json.loads(settings_path.read_text(encoding='utf-8-sig')) if settings_path.is_file() else {}
    except ValueError:
        problems.append('~/.claude/settings.json invalido; nada sera movido.')
        settings = {}
    text = json.dumps({'hooks': settings.get('hooks', {}), 'statusLine': settings.get('statusLine', {})})
    if '/.claude/launcher/' in text.replace('\\\\', '/').replace('\\', '/').casefold():
        problems.append('settings.json ainda chama arquivos do launcher (hooks ou statusLine). Rode o instalador atual antes.')
    if os.path.normcase(str(launcher / 'bin')) in os.path.normcase(path_value):
        problems.append('O PATH do usuario ainda inclui launcher/bin. Rode o instalador atual e reabra o terminal.')
    if sessions is None:
        problems.append('Nao foi possivel listar os processos; nada sera movido.')
    elif sessions:
        problems.append('Sessoes ainda abertas pelo launcher/router: ' + ', '.join(sessions) + '. Feche todas (inclusive o claude atual).')
    return problems


def apply(home, sessions, path_value, stamp=None):
    problems = checks(home, sessions, path_value)
    if problems:
        raise RuntimeError(' | '.join(problems))
    stamp = stamp or datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    root = home / '.claude/launcher/backups' / ('remocao-router-' + stamp)
    if root.exists():
        raise RuntimeError('Pasta de quarentena ja existe: ' + str(root))
    root.mkdir(parents=True)
    if os.name != 'nt':
        root.chmod(0o700)
    else:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
        from core import protect_directory
        protect_directory(root)
    journal_path = root / 'journal.json'
    journal = {'home': str(home), 'quarantine': str(root / 'quarentena'), 'entries': []}

    def save():
        temporary = journal_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(journal, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temporary, journal_path)

    for phase, source in plan(home):
        relative = source.relative_to(home)
        if any(part in NEVER for part in relative.parts):
            raise RuntimeError('Caminho protegido; recusado: ' + str(source))
        destination = root / 'quarentena' / relative
        entry = {'phase': phase, 'source': str(source), 'quarantine': str(destination), 'done': False}
        if is_link(source):
            entry.update(kind='link', target=link_target(source))
        else:
            entry.update(kind='dir' if source.is_dir() else 'file', hashes=file_hashes(source),
                         links=[{'path': str(link), 'target': link_target(link)} for link in inner_links(source)] if source.is_dir() else [])
        journal['entries'].append(entry)
        save()
        if entry['kind'] == 'link':
            remove_link(source)
        else:
            for link in entry['links']:
                remove_link(Path(link['path']))
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
        entry['done'] = True
        save()
    for folder in empty_dirs(home):
        if folder.is_dir() and not is_link(folder) and not any(folder.iterdir()):
            journal['entries'].append({'phase': 'final', 'source': str(folder), 'kind': 'empty-dir', 'done': False})
            save()
            folder.rmdir()
            journal['entries'][-1]['done'] = True
            save()
    journal['complete'] = True
    save()
    return journal_path


def restore(journal_path):
    journal = json.loads(Path(journal_path).read_text(encoding='utf-8'))
    done = [entry for entry in journal['entries'] if entry.get('done')]
    # Check everything first so a refusal never leaves a half-restored installation.
    for entry in done:
        source = Path(entry['source'])
        if entry['kind'] != 'empty-dir' and (source.exists() or is_link(source)):
            raise RuntimeError('Destino ja existe; restauracao recusada: ' + str(source))
        if entry['kind'] in ('file', 'dir') and file_hashes(Path(entry['quarantine'])) != entry['hashes']:
            raise RuntimeError('Conteudo da quarentena mudou; restauracao recusada: ' + entry['quarantine'])
    for entry in reversed(done):
        source = Path(entry['source'])
        if entry['kind'] == 'empty-dir':
            source.mkdir(parents=True, exist_ok=True)
            continue
        if entry['kind'] == 'link':
            source.parent.mkdir(parents=True, exist_ok=True)
            create_link(source, entry['target'])
            continue
        quarantined = Path(entry['quarantine'])
        source.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(quarantined), str(source))
        for link in entry.get('links', []):
            create_link(Path(link['path']), link['target'])
    journal['restored'] = True
    Path(journal_path).write_text(json.dumps(journal, ensure_ascii=False, indent=2), encoding='utf-8')


def report(home, sessions, path_value):
    rows = plan(home)
    print('Itens (em ordem; nada foi alterado):')
    for phase, path in rows:
        kind = 'link' if is_link(path) else ('pasta' if path.is_dir() else 'arquivo')
        extra = ' -> ' + link_target(path) + ' (so o link)' if kind == 'link' else ''
        links = inner_links(path) if kind == 'pasta' else []
        if links:
            extra = ' [links internos removidos como link: ' + ', '.join(str(l.relative_to(path)) for l in links) + ']'
        print(f'  [{phase}] {kind:7} {size(path) / 1024:9.1f} KB  {path}{extra}')
    for folder in empty_dirs(home):
        print('  [final] pasta    (so se ficar vazia)  ' + str(folder))
    print('Nao tocados: ~/.omniroute, chaves OpenRouter, ~/.claude/settings.json e o resto do perfil original.')
    problems = checks(home, sessions, path_value)
    print('Bloqueios para --aplicar agora: ' + ('nenhum' if not problems else ''))
    for problem in problems:
        print('  - ' + problem)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true')
    group.add_argument('--aplicar', action='store_true')
    group.add_argument('--restaurar', type=Path, metavar='JOURNAL')
    parser.add_argument('--home', type=Path, default=Path.home())
    args = parser.parse_args()
    home = args.home.resolve()
    if args.restaurar:
        restore(args.restaurar)
        print('Itens restaurados de ' + str(args.restaurar))
        return 0
    sessions = running_sessions()
    path_value = user_path(home)
    if args.dry_run:
        report(home, sessions, path_value)
        return 0
    journal = apply(home, sessions, path_value)
    print('Concluido. Journal: ' + str(journal))
    print('Para desfazer: python ' + str(Path(__file__).resolve()) + ' --restaurar "' + str(journal) + '"')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print('Remocao interrompida: ' + str(error), file=sys.stderr)
        sys.exit(1)
