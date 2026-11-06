"""Router delegation gate and per-agent model routes; fake upstream only, no model calls."""
import http.client
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
import core
import gateway
import router_gate
from context_config import native_model
from test_profiles import Upstream, catalog

HOOK = ROOT / 'runtime/hook.py'
OUTSIDE = os.path.abspath(os.sep + 'kit-gate-test-extra')
CLEAN = ('CLAUDE_PROJECT_DIR', 'CLAUDE_CONFIG_DIR', 'CLAUDE_PERFIS_RUN')


def clean_env(**extra):
    env = {k: v for k, v in os.environ.items() if k not in CLEAN}
    env.update(extra)
    return env


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cwd = Path(self.temp.name) / 'projeto-ação'
        (self.cwd / 'docs').mkdir(parents=True)
        self.env = patch.dict(os.environ, clean_env(), clear=True)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def event(self, tool, subagent=False, **tool_input):
        data = {'hook_event_name': 'PreToolUse', 'tool_name': tool, 'tool_input': tool_input, 'cwd': str(self.cwd)}
        if subagent:
            data.update(agent_id='a1b2', agent_type='router-coder')
        return data

    def test_main_conversation_cannot_edit_code(self):
        for tool, key in router_gate.EDIT_TOOLS.items():
            reason = router_gate.check(self.event(tool, **{key: str(self.cwd / 'src/app/page.tsx')}))
            self.assertIn('router-coder', reason)
            self.assertIn('page.tsx', reason)

    def test_subagent_may_edit_code(self):
        for tool, key in router_gate.EDIT_TOOLS.items():
            self.assertIsNone(router_gate.check(self.event(tool, subagent=True, **{key: str(self.cwd / 'src/app/page.tsx')})))
        self.assertIsNone(router_gate.check(self.event('Write', subagent=True, file_path='src/components/Hero.tsx')))

    def test_coordinator_exceptions(self):
        for name in ('CONTINUIDADE.md', 'HANDOFF.md', 'PLANO.md', 'docs/PLANO-IMPLEMENTACAO.md', 'docs/plans/fase-1.md', 'src/notas/CONTINUIDADE.md'):
            self.assertIsNone(router_gate.check(self.event('Edit', file_path=str(self.cwd / name))), name)
        for name in ('src/README.md', 'docs/page.tsx', 'package.json', 'CONTINUIDADE.md.bak'):
            self.assertIsNotNone(router_gate.check(self.event('Write', file_path=str(self.cwd / name))), name)

    def test_outside_project_denied_for_everyone(self):
        stray = '/workspaces/projeto-ação/package.json'
        for subagent in (False, True):
            reason = router_gate.check(self.event('Write', subagent=subagent, file_path=stray))
            self.assertIn('fora do projeto', reason)
        self.assertIn('fora do projeto', router_gate.check(self.event('Edit', subagent=True, file_path=os.path.join(OUTSIDE, 'x.tsx'))))

    def test_additional_directories_allowed(self):
        target = os.path.join(OUTSIDE, 'site', 'page.tsx')
        self.assertIsNotNone(router_gate.check(self.event('Write', subagent=True, file_path=target)))
        (self.cwd / '.claude').mkdir()
        (self.cwd / '.claude/settings.local.json').write_text(json.dumps({'permissions': {'additionalDirectories': [OUTSIDE]}}), encoding='utf-8')
        self.assertIsNone(router_gate.check(self.event('Write', subagent=True, file_path=target)))
        # Main conversation still delegates code even inside an authorized folder.
        self.assertIn('router-coder', router_gate.check(self.event('Write', file_path=target)))

    def test_profile_additional_directories_allowed(self):
        config = Path(self.temp.name) / 'router-profile'
        config.mkdir()
        (config / 'settings.json').write_text(json.dumps({'permissions': {'additionalDirectories': [OUTSIDE]}}), encoding='utf-8')
        with patch.dict(os.environ, {'CLAUDE_CONFIG_DIR': str(config)}):
            self.assertIsNone(router_gate.check(self.event('Edit', subagent=True, file_path=os.path.join(OUTSIDE, 'a.css'))))

    @unittest.skipUnless(os.name == 'nt', 'Git Bash drive paths exist only on Windows')
    def test_git_bash_drive_path_is_same_project(self):
        posix = '/' + str(self.cwd)[0].lower() + str(self.cwd)[2:].replace('\\', '/') + '/CONTINUIDADE.md'
        self.assertIsNone(router_gate.check(self.event('Edit', file_path=posix)))

    BLOCKED = (
        ("cat > src/app/page.tsx <<'EOF'\nexport default 1\nEOF", 'redirecionamento', 'src/app/page.tsx'),
        ('echo "body{}" >> styles.css', 'redirecionamento', 'styles.css'),
        ('printf x >"src/a b/Hero.jsx"', 'redirecionamento', 'src/a b/Hero.jsx'),
        ('Set-Content -Path src/lib/x.ts -Value 1', 'Set-Content', 'src/lib/x.ts'),
        ('"<p>" | Out-File "C:\\Projetos\\site\\index.html"', 'Out-File', 'index.html'),
        ("sed -i 's/a/b/' src/app.jsx", 'sed -i', 'src/app.jsx'),
        ("sed -E -i.bak 's/a/b/' tailwind.config.js", 'sed -i', 'tailwind.config.js'),
        ("node -e \"require('fs').writeFileSync('package.json','{}')\"", 'writeFileSync', 'package.json'),
        ('echo x | tee -a src/x.js', 'tee', 'src/x.js'),
        ('node gen.js > public/data.json 2>&1', 'redirecionamento', 'public/data.json'),
    )
    ALLOWED = (
        'npm run build 2>&1', 'npm run build > build.log 2>&1', 'node scripts/check.js > /dev/null',
        'dir > NUL', 'Get-Content x.tsx > $null', 'npx playwright test', 'npx playwright screenshot http://localhost:3000 shot.png',
        'git status', 'git diff -- src/app/page.tsx', 'cat src/app/page.tsx', 'grep -n "a > b" src/x.ts',
        'cat > notas.txt <<EOF\nx\nEOF', 'npm install -D autoprefixer postcss', 'npx tsc --noEmit 2> erros.log',
    )

    def test_shell_writes_blocked_in_main_with_pattern(self):
        for tool in ('Bash', 'PowerShell'):
            for command, pattern, target in self.BLOCKED:
                reason = router_gate.check(self.event(tool, command=command))
                self.assertIsNotNone(reason, command)
                self.assertIn(pattern, reason, command)
                self.assertIn(target, reason, command)
                self.assertIn('router-coder', reason)

    def test_shell_allowed_commands(self):
        for command in self.ALLOWED:
            self.assertIsNone(router_gate.check(self.event('Bash', command=command)), command)

    def test_shell_writes_allowed_in_subagent(self):
        for command, _, _ in self.BLOCKED:
            self.assertIsNone(router_gate.check(self.event('Bash', subagent=True, command=command)), command)

    def test_other_tools_untouched(self):
        for tool in ('Read', 'Grep', 'Glob', 'Skill', 'WebFetch'):
            self.assertIsNone(router_gate.check(self.event(tool, file_path=str(self.cwd / 'a.tsx'))))

    def run_hook(self, event, **env):
        result = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event, ensure_ascii=False).encode('utf-8'),
                                capture_output=True, env=clean_env(CLAUDE_PERFIS_PROFILE='router', **env))
        self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8', 'replace'))
        return json.loads(result.stdout) if result.stdout.strip() else None

    def test_hook_process_denies_main_and_allows_subagent(self):
        target = str(self.cwd / 'src/app/layout.tsx')
        denied = self.run_hook(self.event('Write', file_path=target))['hookSpecificOutput']
        self.assertEqual(denied['permissionDecision'], 'deny')
        self.assertIn('router-coder', denied['permissionDecisionReason'])
        # Silence = normal permission flow, never an automatic approval.
        self.assertIsNone(self.run_hook(self.event('Write', subagent=True, file_path=target)))
        self.assertIsNone(self.run_hook(self.event('Edit', file_path=str(self.cwd / 'CONTINUIDADE.md'))))
        shell = self.run_hook(self.event('Bash', command='echo x > src/app/page.tsx'))['hookSpecificOutput']
        self.assertIn('redirecionamento', shell['permissionDecisionReason'])

    def test_hook_process_original_profile_unaffected(self):
        event = self.event('Write', file_path=str(self.cwd / 'src/app/layout.tsx'))
        result = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event).encode(), capture_output=True,
                                env=clean_env(CLAUDE_PERFIS_PROFILE='original'))
        self.assertEqual(result.returncode, 0)
        self.assertNotIn(b'deny', result.stdout)


class CoordinatorHardeningTests(unittest.TestCase):
    """Skill names, shared kit instructions and parallel agents on the same free models."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cwd = self.root / 'projeto-ação'
        self.cwd.mkdir()
        self.run_dir = self.root / 'run'
        self.run_dir.mkdir()
        self.home = self.root / 'home'
        self.env = patch.dict(os.environ, clean_env(CLAUDE_KIT_HOME=str(self.home)), clear=True)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def hook(self, event, run=True):
        env = clean_env(CLAUDE_PERFIS_PROFILE='router', CLAUDE_KIT_HOME=str(self.home))
        if run:
            env['CLAUDE_PERFIS_RUN'] = str(self.run_dir)
        result = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event, ensure_ascii=False).encode('utf-8'),
                                capture_output=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8', 'replace'))
        return json.loads(result.stdout)['hookSpecificOutput'] if result.stdout.strip() else None

    def agent(self, role, tool_id):
        return {'hook_event_name': 'PreToolUse', 'tool_name': 'Agent', 'tool_use_id': tool_id, 'cwd': str(self.cwd),
                'transcript_path': str(self.root / 'sessao.jsonl'),
                'tool_input': {'subagent_type': role, 'description': 'x', 'prompt': 'y', 'model': 'sonnet', 'effort': 'high'}}

    def test_skill_named_after_router_agent_is_denied(self):
        for name in ('router-coder', '/router-fast', 'kit:router-visual', 'Router-Assistant extra'):
            reason = router_gate.check({'tool_name': 'Skill', 'tool_input': {'skill': name}, 'cwd': str(self.cwd)})
            self.assertIsNotNone(reason, name)
            self.assertIn('Agent(subagent_type="router-', reason)
        for name in ('tailwind-patterns', 'webapp-testing', 'routerish'):
            self.assertIsNone(router_gate.check({'tool_name': 'Skill', 'tool_input': {'skill': name}, 'cwd': str(self.cwd)}), name)
        denied = self.hook({'hook_event_name': 'PreToolUse', 'tool_name': 'Skill', 'tool_input': {'skill': 'router-coder'}, 'cwd': str(self.cwd)})
        self.assertEqual(denied['permissionDecision'], 'deny')

    def test_shared_kit_agents_md_is_not_read(self):
        shared = self.home / '.gemini/config/skills/AGENTS.md'
        shared.parent.mkdir(parents=True)
        shared.write_text('shared rules')
        profile = self.root / 'router-profile'
        (profile / 'skills').mkdir(parents=True)
        (profile / 'skills/AGENTS.md').write_text('shared rules copy')
        with patch.dict(os.environ, {'CLAUDE_CONFIG_DIR': str(profile)}):
            for path in (shared, profile / 'skills/AGENTS.md'):
                reason = router_gate.check({'tool_name': 'Read', 'tool_input': {'file_path': str(path)}, 'cwd': str(self.cwd)})
                self.assertIn('AGENTS.md compartilhado', reason)
            # The project's own instructions stay readable.
            self.assertIsNone(router_gate.check({'tool_name': 'Read', 'tool_input': {'file_path': str(self.cwd / 'AGENTS.md')}, 'cwd': str(self.cwd)}))

    @unittest.skipUnless(os.name == 'nt', 'directory junctions exist only on Windows')
    def test_shared_agents_md_through_junction_is_not_read(self):
        shared = self.home / '.gemini/config/skills'
        shared.mkdir(parents=True)
        (shared / 'AGENTS.md').write_text('shared rules')
        link = self.home / '.claude/profiles/router/skills'
        link.parent.mkdir(parents=True)
        subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(shared)], check=True, capture_output=True)
        try:
            reason = router_gate.check({'tool_name': 'Read', 'tool_input': {'file_path': str(link / 'AGENTS.md')}, 'cwd': str(self.cwd)})
            self.assertIn('AGENTS.md compartilhado', reason)
        finally:
            os.rmdir(link)  # Removes only the junction, never the target's files.
        self.assertTrue((shared / 'AGENTS.md').is_file())

    def test_second_agent_on_shared_models_waits_for_the_first(self):
        first = self.hook(self.agent('router-coder', 'call-1'))
        self.assertEqual(first['permissionDecision'], 'allow')
        self.assertNotIn('model', first['updatedInput'])
        # North Mini Code and Gemma 4 31B are in the coder chain too.
        for role in ('router-fast', 'router-visual', 'router-coder', 'router-assistant'):
            denied = self.hook(self.agent(role, 'call-' + role))
            self.assertEqual(denied['permissionDecision'], 'deny', role)
            self.assertIn('Espere o relatorio', denied['permissionDecisionReason'])
        self.hook({'hook_event_name': 'SubagentStart', 'agent_id': 'a1', 'agent_type': 'router-coder', 'transcript_path': str(self.root / 'sessao.jsonl')})
        self.assertIsNone(self.hook({'hook_event_name': 'SubagentStop', 'agent_id': 'a1', 'agent_type': 'router-coder'}))
        self.assertEqual(self.hook(self.agent('router-fast', 'call-2'))['permissionDecision'], 'allow')

    def test_agents_without_shared_models_may_run_together(self):
        self.assertEqual(self.hook(self.agent('router-visual', 'v1'))['permissionDecision'], 'allow')
        self.assertEqual(self.hook(self.agent('router-fast', 'f1'))['permissionDecision'], 'allow')
        self.assertEqual(self.hook(self.agent('router-assistant', 'a1'))['permissionDecision'], 'deny')

    def test_failed_launch_and_finished_meta_free_the_slot(self):
        self.hook(self.agent('router-coder', 'call-1'))
        self.hook({'hook_event_name': 'PostToolUseFailure', 'tool_name': 'Agent', 'tool_use_id': 'call-1'})
        self.assertEqual(self.hook(self.agent('router-coder', 'call-2'))['permissionDecision'], 'allow')
        # SubagentStop never arrived, but the agent's own meta says it finished.
        self.hook({'hook_event_name': 'SubagentStart', 'agent_id': 'b2', 'agent_type': 'router-coder', 'transcript_path': str(self.root / 'sessao.jsonl')})
        transcript = self.root / 'sessao/subagents/agent-b2.jsonl'
        transcript.parent.mkdir(parents=True)
        transcript.write_text('{}\n')
        self.assertEqual(self.hook(self.agent('router-fast', 'call-3'))['permissionDecision'], 'deny')
        transcript.with_name('agent-b2.meta.json').write_text(json.dumps({'agentType': 'router-coder', 'toolUseId': 'call-2', 'finished': True}))
        self.assertEqual(self.hook(self.agent('router-fast', 'call-3'))['permissionDecision'], 'allow')

    def test_simultaneous_calls_allow_exactly_one(self):
        env = clean_env(CLAUDE_PERFIS_PROFILE='router', CLAUDE_KIT_HOME=str(self.home), CLAUDE_PERFIS_RUN=str(self.run_dir))
        processes = [subprocess.Popen([sys.executable, str(HOOK)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=env) for _ in range(4)]
        for index, process in enumerate(processes):
            process.stdin.write(json.dumps(self.agent('router-coder', 'par-' + str(index))).encode())
            process.stdin.close()
        decisions = [json.loads(process.stdout.read())['hookSpecificOutput']['permissionDecision'] for process in processes]
        for process in processes:
            process.wait()
            process.stdout.close()
        self.assertEqual(sorted(decisions), ['allow', 'deny', 'deny', 'deny'])

    def test_bookkeeping_never_blocks_a_stopping_agent(self):
        (self.run_dir / 'agentes-router.json').write_text('not json')
        for event in ({'hook_event_name': 'SubagentStop', 'agent_id': 'x'}, {'hook_event_name': 'SubagentStart'},
                      {'hook_event_name': 'PostToolUseFailure', 'tool_name': 'Agent', 'tool_use_id': 'z'}):
            self.assertIsNone(self.hook(event))
            self.assertIsNone(self.hook(event, run=False))
        # Without a supervised run directory the guard stays out of the way.
        self.assertEqual(self.hook(self.agent('router-coder', 'n1'), run=False)['permissionDecision'], 'allow')
        self.assertEqual(self.hook(self.agent('router-coder', 'n2'), run=False)['permissionDecision'], 'allow')

    def test_router_instructions_short_with_literal_example_and_verification(self):
        text = (ROOT / 'templates/ROUTER.md').read_text(encoding='utf-8')
        self.assertLess(len(text), 7000)
        for required in ('Agent(subagent_type="router-coder"', 'nunca use Skill("router-coder")', '0 tool uses', 'sem relatorio',
                         'Glob/Grep', 'UMA vez', 'Na segunda falha, pare e avise', 'um agente por vez', 'Nao leia o AGENTS.md compartilhado'):
            self.assertIn(required, text)
        self.assertNotIn('config/skills/AGENTS.md', text)
        for model in core.ROLES['router-coder']:
            self.assertIn(core.MODEL_NAMES[model], text)
        coder = (ROOT / 'templates/router-agents/router-coder.md').read_text(encoding='utf-8')
        self.assertIn('real tool calls', coder)
        self.assertIn(', '.join(core.ROLES['router-coder']), coder)


class AgentModelTests(unittest.TestCase):
    """Each router agent's frontmatter model reaches its own principal through the filter."""

    def setUp(self):
        self.upstream = ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
        self.upstream.seen, self.upstream.statuses, self.upstream.harness_refusal = [], [], False
        threading.Thread(target=self.upstream.serve_forever, daemon=True).start()
        self.gate = gateway.Gateway('TEST-ONLY', catalog(), f'http://127.0.0.1:{self.upstream.server_port}', testing=True, transport='openrouter')
        threading.Thread(target=self.gate.serve_forever, daemon=True).start()

    def tearDown(self):
        self.gate.shutdown(); self.gate.server_close()
        self.upstream.shutdown(); self.upstream.server_close()

    def installed_model(self, role):
        # Same substitution the installer applies to templates/router-agents.
        text = (ROOT / 'templates/router-agents' / (role + '.md')).read_text(encoding='utf-8')
        text = re.sub(r'^model: .+$', 'model: ' + native_model(core.ROLES[role][0]), text, count=1, flags=re.M)
        return re.search(r'^model: (.+)$', text, re.M).group(1).strip()

    def test_every_agent_frontmatter_routes_to_its_principal(self):
        for role, pair in core.ROLES.items():
            model = self.installed_model(role)
            connection = http.client.HTTPConnection('127.0.0.1', self.gate.server_port, timeout=5)
            body = {'model': model, 'max_tokens': 10, 'messages': [{'role': 'user', 'content': 'test'}]}
            connection.request('POST', '/v1/messages', json.dumps(body), {'Authorization': 'Bearer ' + self.gate.token, 'Content-Type': 'application/json'})
            response = connection.getresponse(); response.read(); connection.close()
            self.assertEqual(response.status, 200, role)
            self.assertEqual(self.upstream.seen[-1]['model'], pair[0], role)

    def test_subagent_env_never_forces_one_model(self):
        # Since Claude Code 2.1.251 frontmatter beats CLAUDE_CODE_SUBAGENT_MODEL unless FORCE is set.
        env = core.router_env()
        self.assertNotIn('CLAUDE_CODE_SUBAGENT_MODEL_FORCE', env)
        with patch.dict(os.environ, {'CLAUDE_CODE_SUBAGENT_MODEL_FORCE': '1', 'CLAUDE_CODE_SUBAGENT_MODEL': 'haiku'}):
            child = core.child_env('router')
        self.assertFalse(any(name.startswith('CLAUDE_CODE_SUBAGENT_') for name in child))

    def test_agent_templates_have_role_and_report_contract(self):
        for role in core.ROLES:
            text = (ROOT / 'templates/router-agents' / (role + '.md')).read_text(encoding='utf-8')
            self.assertRegex(text, r'(?m)^name: ' + role + r'$')
            self.assertIn('Relatorio', text)
            self.assertIn('[TEXTO A DEFINIR]', text)
        visual = (ROOT / 'templates/router-agents/router-visual.md').read_text(encoding='utf-8')
        self.assertNotRegex(visual, r'(?m)^tools: .*\b(Edit|Write)\b')
        coder = (ROOT / 'templates/router-agents/router-coder.md').read_text(encoding='utf-8')
        for skill in ('tailwind-patterns', 'nextjs-react-expert', 'design-motion-principles', 'impeccable', 'workflow-ui-ux-pro-max', 'avoid-ai-writing'):
            self.assertIn(skill, coder)
            # Every skill named for the coder must ship in the bundle the router profile receives.
            self.assertTrue((ROOT / 'bundle/skills' / skill / 'SKILL.md').is_file(), skill)
        self.assertNotIn('if installed', coder)

    def test_router_instructions_keep_mandatory_site_gate(self):
        text = (ROOT / 'templates/ROUTER.md').read_text(encoding='utf-8')
        for required in ('postcss.config', 'autoprefixer', '"@tailwind" cru', '1440x900', '390x844', 'webapp-testing',
                         'estilo padrao do navegador', '[TEXTO A DEFINIR]', 'router-visual', 'So declare concluido'):
            self.assertIn(required, text)

    def test_router_instructions_stop_on_route_failure_and_serialize_installs(self):
        text = (ROOT / 'templates/ROUTER.md').read_text(encoding='utf-8')
        for required in ('NAO passe o trabalho a outro especialista', 'qual rota falhou', '503, 429, 504', 'espere a decisao dele',
                         'Apenas um agente por vez roda npm install', 'node_modules ou o lockfile',
                         'Nunca troque a versao de framework', 'Next 15 nao vira 16'):
            self.assertIn(required, text)


if __name__ == '__main__':
    unittest.main()
