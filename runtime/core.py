"""Shared helpers for the installer and its rollback; no credentials are read or logged."""
import base64
import hashlib
import json
import os
import subprocess
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent


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


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
