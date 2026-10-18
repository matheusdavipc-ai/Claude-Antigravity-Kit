"""Use OmniRoute's durable config location, preserving encryption material."""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from core import protect_directory

def entries(text):
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, raw = line.split('=', 1)
            if key.strip(): result.setdefault(key.strip(), raw.strip())
    return result

def parsed(raw):
    match = re.match(r"^(['\"])([\s\S]*)\1\s*(?:#.*)?$", raw)
    return match.group(2) if match else re.split(r'\s#', raw, maxsplit=1)[0].strip()

def configure(home=None, package=None):
    home = Path(home or Path.home()).resolve()
    if package is None:
        npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
        if not npm:
            raise RuntimeError('npm nao encontrado; instale Node.js LTS.')
        result = subprocess.run([npm, 'root', '-g'], capture_output=True, text=True, timeout=20, check=True)
        package = Path(result.stdout.strip()) / 'omniroute'
    package = Path(package).resolve()
    if not (package / 'package.json').is_file() or json.loads((package / 'package.json').read_text(encoding='utf-8')).get('name') != 'omniroute':
        raise RuntimeError('Pacote OmniRoute nao validado.')
    if os.environ.get('DATA_DIR') and Path(os.environ['DATA_DIR']).resolve() != home / '.omniroute':
        raise RuntimeError('DATA_DIR personalizado: preserve essa instalacao e configure-a explicitamente antes de continuar.')
    if os.environ.get('OMNIROUTE_SERVER_HOST', '127.0.0.1') != '127.0.0.1':
        raise RuntimeError('Sobreposicao de host na sessao: defina OMNIROUTE_SERVER_HOST=127.0.0.1.')
    durable, volatile = home / '.omniroute/.env', package / '.env'
    original = durable.read_bytes() if durable.is_file() else b''
    package_data = volatile.read_bytes() if volatile.is_file() else b''
    existing = entries(original.decode('utf-8-sig'))
    # Electron secrets have precedence over package defaults when CLI config is absent.
    electron = home / '.omniroute/server.env'
    if not original and electron.is_file():
        existing.update(entries(electron.read_text(encoding='utf-8-sig')))
    for key, raw in entries(package_data.decode('utf-8-sig')).items():
        existing.setdefault(key, raw)
    if (home / '.omniroute/storage.sqlite').exists() and not parsed(existing.get('STORAGE_ENCRYPTION_KEY', '')) and not os.environ.get('STORAGE_ENCRYPTION_KEY'):
        raise RuntimeError('Banco existente sem chave conhecida: nao gerar outra chave; restaure o segredo correto.')
    updated = dict(existing, OMNIROUTE_SERVER_HOST='127.0.0.1', OMNIROUTE_READY_TIMEOUT_MS='180000')
    text = '# Configuracao persistente. Nao compartilhar este arquivo.\n' + '\n'.join(k + '=' + v for k,v in updated.items()) + '\n'
    if any(parsed(entries(text)[k]) != parsed(v) for k,v in existing.items() if k not in ('OMNIROUTE_SERVER_HOST','OMNIROUTE_READY_TIMEOUT_MS')):
        raise RuntimeError('Valores existentes nao foram preservados; nenhuma escrita.')
    if entries(original.decode('utf-8-sig')) == updated and not entries(package_data.decode('utf-8-sig')):
        print('OmniRoute: configuracao persistente ja esta correta.')
        return
    backup = home / '.omniroute/backups' / ('kit-env-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    protect_directory(backup)
    (backup / 'user.env').write_bytes(original)
    (backup / 'package.env').write_bytes(package_data)
    durable.parent.mkdir(parents=True, exist_ok=True)
    try:
        durable.write_text(text, encoding='utf-8')
        if volatile.exists():
            volatile.write_text('# Personal settings are stored in ~/.omniroute/.env\n', encoding='utf-8')
    except Exception:
        if original: durable.write_bytes(original)
        else: durable.unlink(missing_ok=True)
        if package_data: volatile.write_bytes(package_data)
        raise
    if os.name != 'nt':
        durable.chmod(0o600)
    else:
        script = "$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value; & icacls.exe '" + str(durable).replace("'", "''") + "' /inheritance:r /grant:r ('*'+$sid+':F') | Out-Null; if($LASTEXITCODE){exit 1}"
        subprocess.run(['powershell.exe','-NoProfile','-Command',script],capture_output=True,check=True)
    print('OmniRoute configurado para acesso somente local; chaves existentes preservadas. Reinicie-o se estiver aberto.')

if __name__ == '__main__':
    try:
        configure()
    except Exception as error:
        print('Configuracao do OmniRoute interrompida (' + type(error).__name__ + '). Consulte o README; nao substitua chaves existentes.',file=sys.stderr)
        sys.exit(1)
