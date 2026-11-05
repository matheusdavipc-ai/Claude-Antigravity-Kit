"""Router profile write gate: the coordinator plans; role agents write code.

Only reads the hook event and local settings. Never prints file contents.
"""
import json
import os
import re
import tempfile
from pathlib import Path

EDIT_TOOLS = {'Edit': 'file_path', 'Write': 'file_path', 'MultiEdit': 'file_path', 'NotebookEdit': 'notebook_path'}
SHELL_TOOLS = {'Bash', 'PowerShell'}
# Longer extensions first so ".tsx" is not read as ".ts".
CODE_EXTENSIONS = ('tsx', 'ts', 'jsx', 'json', 'mjs', 'cjs', 'js', 'scss', 'css', 'html', 'htm')
EXCEPTION_NAMES = {'continuidade.md', 'handoff.md'}
DELEGATE = 'Delegue ao router-coder (ou ao router-fast para algo pequeno) usando o Agent com o subagent_type correspondente.'

_EXT = r'\.(?:' + '|'.join(CODE_EXTENSIONS) + r')'
_TARGET = (r'(?:"([^"\n]*' + _EXT + r')"'
           r"|'([^'\n]*" + _EXT + r")'"
           r'|([^\s"\'|;&<>()]*' + _EXT + r'))(?![\w.])')
SHELL_PATTERNS = (
    # A digit, & or > before the operator means 2>&1, &>, or the second char of >>.
    ('redirecionamento > ou >>', re.compile(r'(?<![0-9&>])>>?\s*' + _TARGET)),
    ('Set-Content/Add-Content/Out-File', re.compile(r'(?i)\b(?:Set-Content|Add-Content|Out-File)\b[^|;\n]*?' + _TARGET)),
    ('sed -i', re.compile(r'\bsed\b[^|;\n]*?\s(?:-[a-zA-Z]*i[a-zA-Z]*|--in-place)\b[^|;\n]*?' + _TARGET)),
    ('tee', re.compile(r'\btee\b(?:\s+-{1,2}[\w-]+)*\s+' + _TARGET)),
)
NODE_WRITE = re.compile(r'\b(?:writeFileSync|appendFileSync|writeFile|appendFile)\b')
ANY_TARGET = re.compile(_TARGET)


def _first(match):
    return next(group for group in match.groups() if group)


def shell_write(command):
    """Return (pattern, target) when a shell command writes a code file, else None."""
    command = str(command or '')
    for name, pattern in SHELL_PATTERNS:
        match = pattern.search(command)
        if match:
            return name, _first(match)
    if NODE_WRITE.search(command):
        match = ANY_TARGET.search(command)
        if match:
            return 'writeFileSync/writeFile', _first(match)
    return None


def native_path(value, base):
    text = os.path.expanduser(str(value).strip())
    if os.name == 'nt':
        # Git Bash style /c/<path> is the same drive path for the Windows CLI.
        drive = re.match(r'^/([a-zA-Z])(/.*)?$', text)
        if drive:
            text = drive.group(1) + ':' + (drive.group(2) or '/')
    # On Windows a rootless "/workspaces/x" joins onto the cwd drive, like the CLI does.
    return os.path.normcase(os.path.realpath(os.path.join(str(base), text)))


def _inside(path, root):
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:
        return False


def _settings_dirs(path, base):
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        return []
    directories = (data.get('permissions') or {}).get('additionalDirectories') or []
    return [native_path(item, base) for item in directories if isinstance(item, str) and item.strip()]


def allowed_roots(event):
    cwd = event.get('cwd') or os.getcwd()
    project = os.environ.get('CLAUDE_PROJECT_DIR')
    roots = [native_path(cwd, cwd)]
    if project:
        roots.append(native_path(project, cwd))
    config = os.environ.get('CLAUDE_CONFIG_DIR')
    sources = [Path(cwd) / '.claude/settings.json', Path(cwd) / '.claude/settings.local.json']
    if project:
        sources += [Path(project) / '.claude/settings.json', Path(project) / '.claude/settings.local.json']
    if config:
        sources.append(Path(config) / 'settings.json')
    for source in sources:
        roots += _settings_dirs(source, cwd)
    # Session plumbing: native plan files, the private run directory and system temp.
    if config:
        roots.append(native_path(Path(config) / 'plans', cwd))
    if os.environ.get('CLAUDE_PERFIS_RUN'):
        roots.append(native_path(os.environ['CLAUDE_PERFIS_RUN'], cwd))
    roots.append(native_path(tempfile.gettempdir(), cwd))
    return list(dict.fromkeys(roots))


def coordinator_may_write(path, event):
    """Main conversation may only write continuity, handoff and plan Markdown."""
    name = os.path.basename(path).casefold()
    if name in EXCEPTION_NAMES:
        return True
    if not name.endswith('.md'):
        return False
    cwd = event.get('cwd') or os.getcwd()
    bases = [native_path(cwd, cwd)]
    if os.environ.get('CLAUDE_PROJECT_DIR'):
        bases.append(native_path(os.environ['CLAUDE_PROJECT_DIR'], cwd))
    if os.environ.get('CLAUDE_CONFIG_DIR'):
        if _inside(path, native_path(Path(os.environ['CLAUDE_CONFIG_DIR']) / 'plans', cwd)):
            return True
    if os.environ.get('CLAUDE_PERFIS_RUN') and _inside(path, native_path(os.environ['CLAUDE_PERFIS_RUN'], cwd)):
        return True
    for base in bases:
        if os.path.dirname(path) == base or _inside(path, os.path.join(base, 'docs')):
            return True
    return False


def check(event):
    """Return a denial reason for a router PreToolUse event, or None to continue normally."""
    tool = event.get('tool_name')
    args = event.get('tool_input') or {}
    subagent = bool(event.get('agent_id'))
    cwd = event.get('cwd') or os.getcwd()
    if tool in EDIT_TOOLS:
        raw = args.get(EDIT_TOOLS[tool]) or ''
        if not raw:
            return 'Caminho de arquivo ausente; operacao recusada pelo verificador do router.'
        path = native_path(raw, cwd)
        if not any(_inside(path, root) for root in allowed_roots(event)):
            return ('Escrita fora do projeto bloqueada: ' + str(raw) + ' nao fica dentro de ' + str(cwd) +
                    ' nem de additionalDirectories. Use um caminho dentro da pasta do projeto.')
        if not subagent and not coordinator_may_write(path, event):
            return ('Na conversa principal do router o coordenador planeja e nao edita codigo (' + tool + ' em ' +
                    os.path.basename(path) + '). Permitido aqui: CONTINUIDADE.md, HANDOFF.md e .md na raiz ou em docs/. ' + DELEGATE)
        return None
    if tool in SHELL_TOOLS and not subagent:
        found = shell_write(args.get('command'))
        if found:
            return ('Escrita de codigo via ' + tool + ' bloqueada na conversa principal do router: padrao "' + found[0] +
                    '" em "' + found[1] + '". Use o shell aqui para build, testes, git, npm, npx e Playwright. ' + DELEGATE)
    return None
