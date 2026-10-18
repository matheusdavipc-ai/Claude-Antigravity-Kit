"""Configure a per-machine OpenRouter key without putting it in Git or command arguments."""
import getpass
import os
import sys
import urllib.request
from core import ROUTER, protect_directory, save_secret

def main():
    protect_directory(ROUTER / 'secrets')
    key = getpass.getpass('Chave OpenRouter (entrada oculta; nao cole no chat): ').strip()
    if not key.startswith('sk-or-'):
        raise ValueError('Use uma chave OpenRouter; uma chave local OmniRoute nao serve aqui.')
    request = urllib.request.Request('https://openrouter.ai/api/v1/key', headers={'Authorization': 'Bearer ' + key})
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError('Chave nao validada.')
    path = ROUTER / 'secrets/openrouter.dpapi'
    # macOS uses the stable file path as the Keychain account identifier.
    if os.name == 'nt':
        temporary = path.with_suffix('.new')
        save_secret(temporary, key)
        temporary.replace(path)
    else:
        save_secret(path, key)
    print('Chave armazenada pelo sistema operacional. Nenhuma geracao foi solicitada.')

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Configuracao da chave interrompida (' + type(error).__name__ + ').', file=sys.stderr)
        sys.exit(1)
