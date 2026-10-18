"""Minimal hook events for the supervisor; never stores tool input or prompts."""
import json
import os
import re
import sys
import time
from pathlib import Path
from core import atomic_json, is_quota, ROLES

def main():
    event = json.load(sys.stdin)
    profile = os.environ.get('CLAUDE_PERFIS_PROFILE')
    name = event.get('hook_event_name')
    if profile == 'router' and name == 'PreToolUse' and event.get('tool_name') == 'Agent':
        # Pin named agents; model overrides cannot redirect the requested role.
        args = event.get('tool_input',{})
        role = args.get('subagent_type')
        if role in ROLES:
            # Agent's per-call schema only accepts Anthropic family aliases in this CLI.
            # Omit it so the custom agent's model frontmatter selects the role route.
            args.pop('model',None)
            args.pop('effort',None)
            print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'allow','updatedInput':args}}))
        else:
            print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny',
                'permissionDecisionReason':'Use um dos agentes router-coder, router-visual, router-fast ou router-assistant.'}}))
        return
    directory = os.environ.get('CLAUDE_PERFIS_RUN')
    if not directory:
        return
    root = Path(directory).resolve()
    # Run path is supplied by our launcher, never by stdin.
    safe = {'event':name,'session':event.get('session_id'), 'agent':event.get('agent_id'),
            'tool_id':event.get('tool_use_id'), 'tool':event.get('tool_name'), 'time':time.time()}
    if name == 'PreToolUse':
        args=event.get('tool_input',{})
        command=str(args.get('command',''))
        safe['detached_possible'] = event.get('tool_name') in ('CronCreate','ScheduleWakeup','TeamCreate') or bool(args.get('run_in_background') and event.get('tool_name') in ('Bash','PowerShell')) or bool(
            re.search(r'(?i)\b(?:start-process|start-job|nohup|setsid|disown)\b|&\s*$',command))
    if name == 'SessionStart' and not event.get('agent_id'):
        safe.update({'cwd':event.get('cwd'),'transcript':event.get('transcript_path')})
    if name == 'StopFailure':
        safe['quota'] = is_quota(event)
        safe['error'] = event.get('error')
        if event.get('transcript_path'):
            safe['transcript'] = event['transcript_path']
        safe['cwd'] = event.get('cwd')
    if name in ('Stop','SubagentStop'):
        safe['background'] = bool(event.get('background_tasks'))
        safe['crons'] = bool(event.get('session_crons'))
    if profile == 'original':
        from quota_watch import feedback
        context, ready = feedback(root, event)
        if ready:
            safe.update({'quota':True,'reason':'anthropic_proactive_95','transcript':event.get('transcript_path'),'cwd':event.get('cwd')})
        if context:
            print(json.dumps({'hookSpecificOutput':{'hookEventName':name,'additionalContext':context}}))
    atomic_json(root / (str(time.time_ns())+'-'+str(os.getpid())+'.event.json'),safe)

if __name__ == '__main__':
    try:
        main()
    except Exception:
        # Fail closed for the router Agent gate; no source content in stderr.
        if os.environ.get('CLAUDE_PERFIS_PROFILE') == 'router':
            print('Falha no verificador de agentes do perfil router.',file=sys.stderr)
            sys.exit(2)
        # Missing event cannot authorize a transition.
        sys.exit(1)
