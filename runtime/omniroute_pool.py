"""Configure the local OmniRoute pool through its official authenticated API client."""
import datetime
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit
from core import ROUTER, KIT, MODELS, protect_directory, save_secret, atomic_json

URL = 'http://127.0.0.1:20128'

def require_ready(url=URL):
    target = urlsplit(url)
    if target.scheme != 'http' or target.hostname not in ('127.0.0.1','localhost','::1') or target.username or target.path not in ('','/') or target.query or target.fragment:
        raise RuntimeError('OmniRoute precisa usar um endereco local HTTP sem caminho.')
    try:
        with urllib.request.urlopen(url.rstrip('/')+'/api/health',timeout=5) as response:
            data=json.load(response)
        if data.get('status') != 'ok': raise ValueError('health')
    except (OSError,ValueError):
        raise RuntimeError('OmniRoute nao esta pronto. Execute omniroute, aguarde a inicializacao e tente novamente.') from None

def setup():
    require_ready()
    npm=shutil.which('npm.cmd' if os.name=='nt' else 'npm')
    node=shutil.which('node')
    if not npm or not node: raise RuntimeError('Instale Node.js LTS e OmniRoute antes de configurar o pool.')
    result=subprocess.run([npm,'root','-g'],capture_output=True,text=True,timeout=20,check=True)
    package=Path(result.stdout.strip())/'omniroute'
    if json.loads((package/'package.json').read_text(encoding='utf-8')).get('name')!='omniroute': raise RuntimeError('Pacote OmniRoute invalido.')
    protect_directory(ROUTER/'secrets')
    backup=KIT/'backups'/('omniroute-pool-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    protect_directory(backup)
    secret=ROUTER/'secrets/omniroute.dpapi'
    request={'url':URL,'package':str(package),'models':['openrouter/'+m for m in sorted(MODELS)],'createKey':not secret.exists(),'backup':str(backup/'pool-before.json')}
    result=subprocess.run([node,str(Path(__file__).with_name('omniroute_bridge.mjs'))],input=json.dumps(request),text=True,capture_output=True,timeout=60)
    if result.returncode:
        raise RuntimeError('Configuracao do pool falhou; nenhum segredo foi exibido. Confira servidor, conexao main1 e compatibilidade do OmniRoute.')
    data=json.loads(result.stdout)
    if request['createKey']:
        if not isinstance(data.get('secret'),str) or not data['secret']: raise RuntimeError('OmniRoute nao retornou a chave local.')
        save_secret(secret,data.pop('secret'))
    old=ROUTER/'upstream.json'
    if old.exists(): (backup/'upstream-before.json').write_bytes(old.read_bytes())
    prior=json.loads(old.read_text(encoding='utf-8')) if old.exists() else {}
    atomic_json(old,{'url':URL,'transport':'omniroute','key_id':data.get('key_id') or prior.get('key_id')})
    atomic_json(backup/'result.json',{k:v for k,v in data.items() if k!='secret'})
    print('OmniRoute conectado: '+', '.join(x['name'] for x in data['connections'])+'; prioridade sequencial, somente modelos gratuitos.')
    if len(data['connections'])==1: print('A segunda conta ainda nao existe. Cadastre main2 com prioridade 2 para habilitar a reserva de conta.')
    return data

if __name__=='__main__':
    try: setup()
    except Exception as error:
        print(str(error) if isinstance(error,RuntimeError) else 'Configuracao do pool interrompida; dados privados preservados.',file=sys.stderr)
        sys.exit(1)
