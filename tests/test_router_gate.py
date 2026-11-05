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
        for skill in ('tailwind-patterns', 'nextjs-react-expert', 'design-motion-principles', 'impeccable', 'avoid-ai-writing'):
            self.assertIn(skill, coder)

    def test_router_instructions_keep_mandatory_site_gate(self):
        text = (ROOT / 'templates/ROUTER.md').read_text(encoding='utf-8')
        for required in ('postcss.config', 'autoprefixer', '"@tailwind" cru', '1440x900', '390x844', 'webapp-testing',
                         'estilo padrao do navegador', '[TEXTO A DEFINIR]', 'router-visual', 'So declare concluido'):
            self.assertIn(required, text)


if __name__ == '__main__':
    unittest.main()
