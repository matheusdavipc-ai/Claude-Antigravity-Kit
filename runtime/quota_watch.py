"""Cooperative subscription checkpoint; never interprets context usage as quota."""
import json
import math
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from core import atomic_json, read_json

THRESHOLD = 95
MAX_AGE = 180

def record(data, root):
    if data.get('agent'):
        return
    windows = {}
    now = time.time()
    for name in ('five_hour', 'seven_day'):
        row = (data.get('rate_limits') or {}).get(name) or {}
        used, reset = row.get('used_percentage'), row.get('resets_at')
        if (type(used) in (int, float) and math.isfinite(used) and 0 <= used <= 100
                and type(reset) in (int, float) and math.isfinite(reset) and reset > now):
            windows[name] = {'used_percentage': used, 'resets_at': reset}
    previous = read_json(root/'quota-telemetry.json', {})
    session = data.get('session_id')
    if previous.get('session') == session and previous.get('windows') == windows:
        now = previous.get('time',now)
    atomic_json(root/'quota-telemetry.json', {'time':now, 'session':session, 'windows':windows})

def approaching(root, session):
    data = read_json(root/'quota-telemetry.json', {})
    now = time.time()
    if not session or data.get('session') != session or not 0 <= now-data.get('time',0) <= MAX_AGE:
        return False
    return any(row.get('used_percentage',0) >= THRESHOLD and row.get('resets_at',0) > now
               for row in data.get('windows',{}).values())

def feedback(root, event):
    """Returns (context, ready). Ready is only emitted at a normal main Stop."""
    if event.get('agent_id'):
        return None, False
    session = event.get('session_id')
    request = read_json(root/'quota-request.json', {})
    try:
        decision = read_json(root/'quota-decision.json', {})
        if not isinstance(decision,dict) or (root/'quota-decision.json').is_symlink():
            decision = {}
    except (ValueError,OSError):
        # The agent may still be writing the decision; this cannot authorize closure.
        decision = {}
    requested = request.get('session') == session and bool(session)
    if event.get('hook_event_name') == 'UserPromptSubmit':
        if decision.get('action') == 'complete':
            for name in ('quota-request.json','quota-decision.json'):
                (root/name).unlink(missing_ok=True)
        return None, False
    if not requested and not approaching(root, session):
        return None, False
    if requested and decision.get('session_id') == session:
        if decision.get('action') == 'complete':
            return None, False
        checkpoint = root/'HANDOFF.md'
        if (decision.get('action') == 'transfer' and checkpoint.is_file() and not checkpoint.is_symlink()
                and 0 < checkpoint.stat().st_size <= 100000
                and checkpoint.stat().st_mtime >= request.get('time',0)
                and (root/'quota-decision.json').stat().st_mtime >= request.get('time',0)):
            ready = event.get('hook_event_name') == 'Stop' and not event.get('background_tasks') and not event.get('session_crons')
            return None, ready
    name = event.get('hook_event_name')
    if name not in ('PostToolUse','Stop'):
        return None, False
    # At most one tool reminder and one Stop continuation, never an infinite Stop loop.
    if requested and (name != 'Stop' or request.get('stop_reminded') or event.get('stop_hook_active')):
        return None, False
    if not requested:
        request = {'session':session, 'time':time.time()}
    request['stop_reminded'] = name == 'Stop' or request.get('stop_reminded',False)
    atomic_json(root/'quota-request.json', request)
    text = (
        'A telemetria da assinatura Anthropic atingiu 95% ou mais em uma janela. '
        'Avalie o trabalho: se falta apenas finalizar e verificar o que ja esta praticamente pronto, conclua agora; '
        'caso contrario, nao inicie novas etapas extensas. Aguarde agentes e tarefas em segundo plano, '
        'verifique operacoes incertas e prepare a continuidade. Nao altere permissoes nem ignore aprovacao obrigatoria. '
        'Registre objetivo, instrucoes do usuario, progresso, arquivos, verificacoes, pendencias, '
        'operacoes incertas e proxima acao em '+str(root/'HANDOFF.md')+'. Sem segredos ou raciocinio interno. '
        'Depois escreva '+str(root/'quota-decision.json')+' com JSON '+
        json.dumps({'session_id':session,'action':'transfer'})+'. Termine o turno apos salvar. '
        'Se a tarefa foi realmente concluida, escreva o mesmo JSON com action complete; nao transfira trabalho concluido. '
        'A estimativa de tempo cabe a voce; 5% nao garante quantidade fixa de tokens. '
        'Se o usuario autorizou trabalho autonomo, adie duvidas opcionais; bloqueios e permissoes obrigatorias continuam valendo.')
    return text, False

def statusline_command(root, previous):
    previous = previous if isinstance(previous,dict) else {}
    atomic_json(root/'previous-statusline.json', previous or {})
    args = [sys.executable, str(Path(__file__).with_name('quota_watch.py'))]
    # Claude executes statusLine through its shell; forward slashes work in Git Bash and POSIX.
    return {**previous, 'type':'command','command':' '.join(shlex.quote(a.replace(chr(92),'/')) for a in args), 'refreshInterval':5}

def main():
    raw = sys.stdin.read()
    data = json.loads(raw)
    root = Path(os.environ['CLAUDE_PERFIS_RUN'])
    record(data, root)
    previous = read_json(root/'previous-statusline.json', {})
    command = previous.get('command') if previous.get('type') == 'command' else None
    if command:
        if os.name == 'nt':
            candidates = [Path(os.environ.get('ProgramFiles','C:/Program Files'))/'Git/bin/bash.exe']
            git = shutil.which('git')
            if git: candidates.insert(0, Path(git).parent.parent/'bin/bash.exe')
            bash = next((str(p) for p in candidates if p.is_file()), None)
            if not bash:
                print('Cota monitorada; status anterior requer Git Bash.')
                return
            args = [bash,'-c',command]
        else:
            args = ['/bin/sh','-c',command]
        try:
            result = subprocess.run(args,input=raw,text=True,capture_output=True,timeout=3)
            print(result.stdout[:20000],end='')
        except (OSError,subprocess.TimeoutExpired):
            pass
    else:
        windows = read_json(root/'quota-telemetry.json',{}).get('windows',{})
        print(' | '.join(name+': '+str(row['used_percentage'])+'%' for name,row in windows.items()) or 'Cota Anthropic: aguardando telemetria')

if __name__ == '__main__':
    try:
        main()
    except Exception:
        # No raw JSON or credentials in diagnostics.
        print('Cota Anthropic: telemetria indisponivel')
