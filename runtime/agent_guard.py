"""One router agent at a time per shared free model.

Two agents whose role chains share a model compete for the same provider limit; in the
real test both died (429 and 504). The coordinator's Agent call is denied while such an
agent runs. State lives in the private run directory and only holds roles, ids and times.
"""
import json
import os
import time
from pathlib import Path
from core import ROLES

STATE = 'agentes-router.json'
LOCK_SECONDS = 5
# An entry left behind by a crash stops blocking after this long.
ENTRY_SECONDS = 45 * 60
IDLE_SECONDS = 10 * 60


def overlaps(first, second):
    return bool(set(ROLES.get(first, ())) & set(ROLES.get(second, ())))


class _Lock:
    """Exclusive file lock: parallel Agent calls in one message run their hooks at once."""

    def __init__(self, path):
        self.path = path
        self.held = False

    def __enter__(self):
        end = time.monotonic() + LOCK_SECONDS
        while time.monotonic() < end:
            try:
                os.close(os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                self.held = True
                return self
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(self.path) > LOCK_SECONDS * 2:
                        os.unlink(self.path)  # Left by a killed hook process.
                        continue
                except OSError:
                    pass
                time.sleep(.05)
        return self

    def __exit__(self, *exc):
        if self.held:
            try:
                os.unlink(self.path)
            except OSError:
                pass


def _load(path):
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        entries = data.get('entries') if isinstance(data, dict) else None
        return [e for e in entries if isinstance(e, dict)] if isinstance(entries, list) else []
    except (OSError, ValueError):
        return []


def _save(path, entries):
    temporary = Path(str(path) + '.' + str(os.getpid()) + '.tmp')
    temporary.write_text(json.dumps({'entries': entries}), encoding='utf-8')
    os.replace(temporary, path)


def _alive(entry, now):
    if now - float(entry.get('time', 0)) >= ENTRY_SECONDS:
        return False
    transcript = entry.get('transcript')
    if not transcript:
        return True
    meta = Path(str(transcript)[:-len('.jsonl')] + '.meta.json')
    try:
        if json.loads(meta.read_text(encoding='utf-8')).get('finished') is True:
            return False
    except (OSError, ValueError, AttributeError):
        pass
    try:
        # No transcript activity for this long: the agent died without SubagentStop.
        return now - os.path.getmtime(transcript) < IDLE_SECONDS
    except OSError:
        return True


def _fresh(entries, now):
    return [e for e in entries if _alive(e, now)]


def subagent_transcript(event, agent):
    # <project>/<session>.jsonl -> <project>/<session>/subagents/agent-<id>.jsonl
    parent = event.get('transcript_path')
    if not parent or not str(parent).endswith('.jsonl'):
        return None
    return str(Path(str(parent)[:-len('.jsonl')]) / 'subagents' / ('agent-' + str(agent) + '.jsonl'))


def claim(run, role, tool_id):
    """Return a denial reason, or None after recording this launch."""
    run = Path(run)
    path = run / STATE
    with _Lock(str(path) + '.lock') as lock:
        if not lock.held:
            return None  # Never block delegation because of the bookkeeping itself.
        now = time.time()
        entries = _fresh(_load(path), now)
        for entry in entries:
            if overlaps(entry.get('role'), role):
                age = int(now - float(entry['time']))
                return ('Ja ha um agente ' + str(entry['role']) + ' em andamento (iniciado ha ' + str(age) + ' s) que usa os mesmos '
                        'modelos gratuitos de ' + role + '. Espere o relatorio dele antes de chamar outro agente: agentes em '
                        'paralelo gastam o mesmo limite do provedor. Uma tarefa por agente; install e build nunca em paralelo.')
        entries.append({'tool': tool_id, 'role': role, 'time': now, 'agent': None, 'transcript': None})
        _save(path, entries)
    return None


def started(run, event):
    role, agent = event.get('agent_type'), event.get('agent_id')
    if role not in ROLES or not agent:
        return
    path = Path(run) / STATE
    with _Lock(str(path) + '.lock') as lock:
        if not lock.held:
            return
        entries = _load(path)
        for entry in entries:
            if entry.get('role') == role and not entry.get('agent'):
                entry['agent'] = agent
                entry['transcript'] = subagent_transcript(event, agent)
                _save(path, entries)
                return


def _meta_tool(event):
    # The native CLI writes <transcript>.meta.json with the Agent call id next to each transcript.
    transcript = event.get('agent_transcript_path')
    if not transcript:
        return None
    try:
        meta = json.loads(Path(str(transcript)[:-len('.jsonl')] + '.meta.json').read_text(encoding='utf-8'))
        return meta.get('toolUseId')
    except (OSError, ValueError, AttributeError):
        return None


def finished(run, event):
    """SubagentStop: free the slot of the agent that ended."""
    path = Path(run) / STATE
    with _Lock(str(path) + '.lock') as lock:
        if not lock.held:
            return
        entries = _load(path)
        agent, role, tool = event.get('agent_id'), event.get('agent_type'), _meta_tool(event)
        match = (next((e for e in entries if agent and e.get('agent') == agent), None)
                 or next((e for e in entries if tool and e.get('tool') == tool), None)
                 or next((e for e in entries if role and e.get('role') == role), None))
        if match:
            entries.remove(match)
            _save(path, entries)


def failed(run, tool_id):
    """PostToolUseFailure on Agent: the launch never happened."""
    path = Path(run) / STATE
    with _Lock(str(path) + '.lock') as lock:
        if not lock.held:
            return
        entries = _load(path)
        kept = [e for e in entries if e.get('tool') != tool_id]
        if len(kept) != len(entries):
            _save(path, kept)
