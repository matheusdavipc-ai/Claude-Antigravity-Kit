"""Local profiles: explicit free-model routes, no credential or prompt logging."""
import base64
import sys
import shlex
import hashlib
import ctypes
import json
import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path
from context_config import context_plan, context_env, context_settings, context_picker, native_model

KIT = Path(__file__).resolve().parent.parent
HOME = Path(os.environ.get('CLAUDE_KIT_HOME') or Path.home())
PYTHON = Path(sys.executable)
EXE = HOME / '.local/bin' / ('claude.exe' if os.name == 'nt' else 'claude')
if (KIT / 'config.json').is_file():
    EXE = Path(json.loads((KIT / 'config.json').read_text(encoding='utf-8'))['native_executable'])
ROUTER = HOME / '.claude/profiles/router'
ROLES = {
    'router-orchestrator': ('thinkingmachines/inkling:free', 'nvidia/nemotron-3-ultra-550b-a55b:free'),
    'router-coder': ('thinkingmachines/inkling-small:free', 'poolside/laguna-s-2.1:free'),
    'router-visual': ('nvidia/nemotron-3.5-super-vl:free', 'thinkingmachines/inkling-small:free'),
    'router-fast': ('cohere/north-mini-code:free', 'poolside/laguna-xs-2.1:free'),
    'router-assistant': ('poolside/laguna-xs-2.1:free', 'cohere/north-mini-code:free'),
}
MODELS = set(m for pair in ROLES.values() for m in pair)

MODEL_NAMES = {'thinkingmachines/inkling:free': 'Inkling', 'thinkingmachines/inkling-small:free': 'Inkling Small', 'nvidia/nemotron-3.5-super-vl:free': 'Nemotron 3.5 Super VL', 'cohere/north-mini-code:free': 'North Mini Code', 'poolside/laguna-xs-2.1:free': 'Laguna XS 2.1', 'nvidia/nemotron-3-ultra-550b-a55b:free': 'Nemotron 3 Ultra', 'poolside/laguna-s-2.1:free': 'Laguna S 2.1'}
PRIMARY_ROLES = {pair[0]: role for role, pair in ROLES.items()}
MODEL_DESCRIPTIONS = {'thinkingmachines/inkling:free': 'Orquestrador Principal', 'thinkingmachines/inkling-small:free': 'Programador Principal; Especialista Visual Reserva', 'nvidia/nemotron-3.5-super-vl:free': 'Especialista Visual Principal', 'cohere/north-mini-code:free': 'Executor Rápido Principal; Programador Auxiliar Reserva', 'poolside/laguna-xs-2.1:free': 'Programador Auxiliar Principal; Executor Rápido Reserva', 'nvidia/nemotron-3-ultra-550b-a55b:free': 'Orquestrador Reserva', 'poolside/laguna-s-2.1:free': 'Programador Principal Reserva'}
PICKER = {'replaceBuiltInOptions': True, 'options': [
    {'model': model, 'label': name, 'description': MODEL_DESCRIPTIONS[model]}
    for model, name in MODEL_NAMES.items()
]}

def router_env(plan=None):
    env = {
        'ANTHROPIC_DEFAULT_OPUS_MODEL': ROLES['router-orchestrator'][0],
        'ANTHROPIC_DEFAULT_SONNET_MODEL': ROLES['router-coder'][0],
        'ANTHROPIC_DEFAULT_HAIKU_MODEL': ROLES['router-fast'][0],
        'ANTHROPIC_DEFAULT_FABLE_MODEL': ROLES['router-orchestrator'][1],
        'CLAUDE_CODE_SUBAGENT_MODEL': ROLES['router-coder'][0],
        'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1',
    }
    for family in ('OPUS','SONNET','HAIKU','FABLE'):
        key = 'ANTHROPIC_DEFAULT_' + family + '_MODEL'
        env[key + '_NAME'] = MODEL_NAMES[env[key]]
        env[key] = native_model(env[key], plan)
        env[key + '_DESCRIPTION'] = 'Equipe OpenRouter gratuita; reservas conforme funcao'
    env['CLAUDE_CODE_SUBAGENT_MODEL'] = native_model(env['CLAUDE_CODE_SUBAGENT_MODEL'], plan)
    env.update(context_env(plan))
    return env


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except FileNotFoundError:
        return default

def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temporary, path)

def protect_directory(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    if os.name != 'nt':
        path.chmod(0o700)
        return
    literal = str(path).replace("'", "''")
    command = "$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value; & icacls.exe '"+literal+"' /inheritance:r /grant:r ('*'+$sid+':(OI)(CI)F') | Out-Null; if($LASTEXITCODE){exit 1}"
    result = subprocess.run(['powershell.exe','-NoProfile','-EncodedCommand', base64.b64encode(command.encode('utf-16-le')).decode()], capture_output=True)
    if result.returncode:
        raise RuntimeError('Falha ao proteger diretorio; operacao interrompida.')

class Blob(ctypes.Structure):
    _fields_ = [('size', ctypes.c_ulong), ('data', ctypes.POINTER(ctypes.c_ubyte))]

def dpapi(data, decrypt=False):
    buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    source = Blob(len(data), buffer)
    output = Blob()
    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    crypt.CryptProtectData.argtypes = [ctypes.POINTER(Blob),ctypes.c_wchar_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong,ctypes.POINTER(Blob)]
    crypt.CryptUnprotectData.argtypes = [ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong,ctypes.POINTER(Blob)]
    if decrypt:
        success = crypt.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(output))
    else:
        success = crypt.CryptProtectData(ctypes.byref(source), 'Claude router local', None, None, None, 1, ctypes.byref(output))
    if not success:
        raise RuntimeError('DPAPI falhou; nenhuma credencial sera exibida.')
    try:
        return ctypes.string_at(output.data, output.size)
    finally:
        kernel.LocalFree(output.data)

def keychain_account(path):
    return hashlib.sha256(str(Path(path).resolve()).encode()).hexdigest()[:24]

def save_secret(path, value):
    path = Path(path)
    if os.name == 'nt':
        path.write_bytes(base64.b64encode(dpapi(value.encode('utf-8'))))
        return
    if sys.platform != 'darwin':
        raise RuntimeError('Somente Windows e macOS sao suportados.')
    if not re.fullmatch(r'sk-[A-Za-z0-9_-]+', value):
        raise ValueError('Formato de chave invalido.')
    account = keychain_account(path)
    # Feed the secret via stdin, never command-line arguments or environment.
    command = 'add-generic-password -U -s claude-openrouter-kit -a ' + account + ' -w ' + value + '\n'
    result = subprocess.run(['/usr/bin/security', '-i'], input=command.encode(), capture_output=True)
    if result.returncode:
        raise RuntimeError('Nao foi possivel salvar no Keychain; nenhuma alternativa em texto puro.')
    path.write_text('keychain:' + account, encoding='utf-8')
    path.chmod(0o600)

def load_secret(path):
    path = Path(path)
    if os.name == 'nt':
        return dpapi(base64.b64decode(path.read_bytes()), decrypt=True).decode('utf-8')
    if sys.platform != 'darwin':
        raise RuntimeError('Somente Windows e macOS sao suportados.')
    marker = path.read_text(encoding='utf-8')
    if not marker.startswith('keychain:'):
        raise RuntimeError('Referencia do Keychain invalida.')
    result = subprocess.run(['/usr/bin/security','find-generic-password','-s','claude-openrouter-kit','-a',marker.split(':',1)[1],'-w'],capture_output=True)
    if result.returncode:
        raise RuntimeError('Desbloqueie o Keychain e autorize o acesso a chave.')
    return result.stdout.decode().strip()


def redact(text):
    text = re.sub(r'(?i)\bsk-[A-Za-z0-9_-]+', '[CREDENCIAL OMITIDA]', str(text))
    text = re.sub(r'(?i)(bearer\s+)[A-Za-z0-9._-]+', r'\1[OMITIDO]', text)
    text = re.sub(r'(?i)((?:api[_-]?key|token|password|secret|authorization)["\s]*[:=]["\s]*)([^\s,}\"]+)', r'\1[OMITIDO]', text)
    return text

def is_quota(event):
    if event.get('error') != 'rate_limit':
        return False
    details = json.dumps(event.get('error_details', ''), ensure_ascii=False) + ' ' + str(event.get('last_assistant_message', ''))
    details = details.lower()
    # Never switch for a family-only limit or a generic 429.
    if re.search(r'(opus|sonnet).{0,45}(limit|quota)|(?:limit|quota).{0,45}(opus|sonnet)', details):
        return False
    return bool(re.search(r"you(?:'|’)?ve (?:hit|reached) your (?:weekly |session |usage )?limit|weekly (?:usage )?limit (?:reached|exceeded)|(?:session|subscription|plan) (?:usage )?(?:limit|quota) (?:reached|exceeded|exhausted)|usage_limit_reached|weekly_limit_reached|session_limit_reached", details))

def child_env(profile):
    env = dict(os.environ)
    # Only the child's environment changes. Saved OAuth remains in the original profile.
    for name in list(env):
        if name.startswith(('ANTHROPIC_', 'OPENROUTER_', 'CLAUDE_CODE_OAUTH', 'CLAUDE_CODE_USE_', 'CLAUDE_CODE_SUBAGENT_', 'CLAUDE_CODE_EFFORT_')) or name in ('CLAUDE_CONFIG_DIR','CLAUDE_CODE_ALWAYS_ENABLE_EFFORT','CLAUDE_CODE_PROJECT_DIR_NAME','CLAUDE_CODE_MAX_CONTEXT_TOKENS','CLAUDE_CODE_DISABLE_1M_CONTEXT'):
            env.pop(name, None)
    env['CLAUDE_CONFIG_DIR'] = str(HOME / ('.claude' if profile == 'original' else '.claude/profiles/router'))
    env['CLAUDE_PERFIS_PROFILE'] = profile
    return env

def get_catalog():
    request = urllib.request.Request('https://openrouter.ai/api/v1/models', headers={'User-Agent':'ClaudePerfis-Local/1.0'})
    with urllib.request.urlopen(request, timeout=20) as response:
        catalog = json.load(response)
    result = {}
    for model in catalog.get('data', []):
        if model['id'] not in MODELS:
            continue
        pricing = model.get('pricing', {})
        # Check every metered dimension; accept only zero (not missing prompt/completion).
        free = all(float(pricing.get(key, '-1')) == 0 for key in ('prompt','completion'))
        free = free and all(float(value) == 0 for value in pricing.values() if isinstance(value, (str, int, float)))
        result[model['id']] = {
            'free': free, 'context': min(v for v in (model.get('context_length', 0), (model.get('top_provider') or {}).get('context_length', model.get('context_length', 0))) if isinstance(v, int) and v > 0) if model.get('context_length', 0) else 0,
            'max_output': (model.get('top_provider') or {}).get('max_completion_tokens'),
            'tools': 'tools' in model.get('supported_parameters', []),
            'modalities': model.get('architecture',{}).get('input_modalities',[]),
            'expires': model.get('expiration_date'),
        }
    return result

def safe_candidate(model, catalog, visual=False):
    item = catalog.get(model, {})
    expiry = item.get('expires')
    return (model in MODELS and model.endswith(':free') and item.get('free') is True
            and item.get('tools') is True and (not visual or 'image' in item.get('modalities', []))
            and (not expiry or expiry > time.strftime('%Y-%m-%d', time.gmtime())))


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
