"""Restore journaled files only when their installed versions are unchanged."""
import json
import os
import shutil
from pathlib import Path
from core import KIT, atomic_json, file_hash, read_json

def rollback():
    state = read_json(KIT / 'installation.json')
    if not state:
        raise RuntimeError('Registro de instalacao ausente.')
    for entry in state['files']:
        path = Path(entry['path'])
        expected = entry.get('installed') or entry.get('planned')
        if path.exists() and expected and file_hash(path) != expected:
            raise RuntimeError('Arquivo alterado depois da instalacao; reversao recusada: ' + str(path))
    for entry in reversed(state['files']):
        path = Path(entry['path'])
        if entry.get('backup'):
            shutil.copy2(entry['backup'], path)
        elif path.is_file():
            path.unlink()
    if os.name == 'nt' and state.get('path_before') is not None:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as registry:
            current, kind = winreg.QueryValueEx(registry, 'Path')
            if current == state.get('path_installed'):
                winreg.SetValueEx(registry, 'Path', 0, kind, state['path_before'])
            else:
                owned = str(KIT / 'bin').casefold()
                winreg.SetValueEx(registry, 'Path', 0, kind, ';'.join(x for x in current.split(';') if x.casefold() != owned))
    state['rolled_back'] = True
    atomic_json(KIT / 'installation.json', state)
    print('Arquivos registrados restaurados. Historicos, credenciais, diretorios e links preservados.')

if __name__ == '__main__':
    rollback()
