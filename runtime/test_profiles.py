import http.client
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
import core
import gateway
import launcher
import rollback

def catalog():
    return {model:{'free':True,'tools':True,'modalities':['text','image'],'context':1000000,'max_output':65536,'expires':None} for model in core.MODELS}

class Upstream(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.seen.append(body)
        status = self.server.statuses.pop(0) if self.server.statuses else 200
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        self.end_headers()
        payload={'model':body['model'],'content':[{'type':'text','text':'ok'}]}
        if status == 403 and self.server.harness_refusal:
            payload={'error':{'message':body['model']+' is only available on agentic harnesses'}}
        self.wfile.write(json.dumps(payload).encode())

class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.upstream = ThreadingHTTPServer(('127.0.0.1',0),Upstream)
        self.upstream.seen=[]
        self.upstream.statuses=[]
        self.upstream.harness_refusal=False
        threading.Thread(target=self.upstream.serve_forever,daemon=True).start()
        self.gate = gateway.Gateway('TEST-ONLY',catalog(),f'http://127.0.0.1:{self.upstream.server_port}',testing=True)
        threading.Thread(target=self.gate.serve_forever,daemon=True).start()
    def tearDown(self):
        self.gate.shutdown(); self.gate.server_close()
        self.upstream.shutdown(); self.upstream.server_close()
    def request(self,model='router-coder',token=None,**extra):
        connection=http.client.HTTPConnection('127.0.0.1',self.gate.server_port,timeout=5)
        body={'model':model,'max_tokens':10,'messages':[{'role':'user','content':'test'}],**extra}
        connection.request('POST','/v1/messages',json.dumps(body),{'Authorization':'Bearer '+(self.gate.token if token is None else token),'Content-Type':'application/json'})
        response=connection.getresponse(); status=response.status; data=response.read(); connection.close()
        return status,data
    def test_paid_model_blocked_before_upstream(self):
        self.assertEqual(self.request('anthropic/claude-opus-5.5')[0],403)
        self.assertEqual(self.upstream.seen,[])
    def test_wrong_auth_blocked(self):
        self.assertEqual(self.request(token='wrong')[0],401)
        self.assertEqual(self.upstream.seen,[])
    def test_every_role_principal(self):
        for role,pair in core.ROLES.items():
            self.assertEqual(self.request(role)[0],200)
            self.assertEqual(self.upstream.seen[-1]['model'],pair[0])
    def test_every_role_reserve_on_unavailable(self):
        for role,pair in core.ROLES.items():
            self.upstream.statuses=[503,200]
            self.assertEqual(self.request(role)[0],200)
            self.assertEqual([r['model'] for r in self.upstream.seen[-2:]],list(pair))
    def test_auth_error_never_tries_reserve(self):
        self.upstream.statuses=[401,200]
        self.assertEqual(self.request()[0],401)
        self.assertEqual(len(self.upstream.seen),1)
    def test_model_harness_restriction_uses_prescribed_reserve(self):
        self.upstream.harness_refusal=True
        self.upstream.statuses=[403,200]
        self.assertEqual(self.request()[0],200)
        self.assertEqual([r['model'] for r in self.upstream.seen],list(core.ROLES['router-coder']))
    def test_changed_price_blocks_model(self):
        for model in core.ROLES['router-coder']:
            self.gate.catalog[model]['free']=False
        self.assertEqual(self.request()[0],503)
        self.assertEqual(self.upstream.seen,[])
    def test_visual_never_falls_to_text_only(self):
        self.gate.catalog[core.ROLES['router-visual'][1]]['modalities']=['text']
        self.upstream.statuses=[503,200]
        self.assertEqual(self.request('router-visual')[0],503)
        self.assertEqual(len(self.upstream.seen),1)
    def test_paid_features_and_effort_removed(self):
        self.assertEqual(self.request(plugins=[{'id':'web'}],thinking={'type':'enabled'},output_config={'effort':'xhigh'},tools=[{'type':'web_search_20250305','name':'web_search'},{'name':'echo','input_schema':{'type':'object'}}])[0],200)
        body=self.upstream.seen[-1]
        for field in ('plugins','thinking','output_config'): self.assertNotIn(field,body)
        self.assertEqual(len(body['tools']),1)
        self.assertEqual(self.gate.active,0)
    def test_expired_principal_selects_only_its_reserve(self):
        self.gate.catalog[core.ROLES['router-coder'][0]]['expires']='2000-01-01'
        self.assertEqual(self.request()[0],200)
        self.assertEqual(self.upstream.seen[-1]['model'],core.ROLES['router-coder'][1])

class SafetyTests(unittest.TestCase):
    def test_quota_detection(self):
        for text in ("You've hit your limit · resets 5pm",'weekly usage limit exceeded','session_limit_reached'):
            self.assertTrue(core.is_quota({'error':'rate_limit','last_assistant_message':text}))
        for error,text in [('rate_limit','429 Too Many Requests'),('authentication_failed',"You've hit your limit"),('rate_limit','Opus weekly limit reached'),('overloaded','weekly limit exceeded')]:
            self.assertFalse(core.is_quota({'error':error,'last_assistant_message':text}))
    def test_env_isolation(self):
        with patch.dict(os.environ,{'ANTHROPIC_AUTH_TOKEN':'fake','CLAUDE_CONFIG_DIR':'bad','CLAUDE_CODE_MAX_CONTEXT_TOKENS':'123','CLAUDE_CODE_DISABLE_1M_CONTEXT':'1'}):
            env=core.child_env('original')
            self.assertNotIn('ANTHROPIC_AUTH_TOKEN',env)
            self.assertNotIn('CLAUDE_CODE_MAX_CONTEXT_TOKENS',env)
            self.assertNotIn('CLAUDE_CODE_DISABLE_1M_CONTEXT',env)
            self.assertEqual(os.environ['ANTHROPIC_AUTH_TOKEN'],'fake')
            self.assertEqual(Path(env['CLAUDE_CONFIG_DIR']),core.HOME / '.claude')
    def test_activity_blocks_inflight(self):
        state=launcher.Activity()
        state.consume({'event':'PreToolUse','tool_id':'a'})
        self.assertFalse(state.idle())
        state.consume({'event':'PostToolUse','tool_id':'a'})
        self.assertTrue(state.idle())
        state.consume({'event':'SubagentStart','agent':'b'})
        self.assertFalse(state.idle())
        state.consume({'event':'SubagentStop','agent':'b','background':False,'crons':False})
        self.assertTrue(state.idle())
    def test_unknown_tool_identity_blocks(self):
        state=launcher.Activity(); state.consume({'event':'PreToolUse'})
        self.assertFalse(state.idle())
    def test_detached_jobs_prevent_automatic_shutdown(self):
        state=launcher.Activity()
        state.consume({'event':'PreToolUse','tool_id':'background','detached_possible':True})
        state.consume({'event':'PostToolUse','tool_id':'background'})
        self.assertFalse(state.idle())
    def test_router_hook_uses_agent_definition_not_invalid_model_override(self):
        env=dict(os.environ,CLAUDE_PERFIS_PROFILE='router')
        event={'hook_event_name':'PreToolUse','tool_name':'Agent','tool_input':{'subagent_type':'router-fast','model':'sonnet','effort':'xhigh','prompt':'synthetic fixture'}}
        result=subprocess.run([sys.executable,str(core.KIT/'runtime/hook.py')],input=json.dumps(event),text=True,capture_output=True,env=env)
        data=json.loads(result.stdout)['hookSpecificOutput']
        self.assertNotIn('model',data['updatedInput'])
        self.assertNotIn('effort',data['updatedInput'])
        self.assertEqual(data['updatedInput']['subagent_type'],'router-fast')
    def test_rollback_restores_original_and_refuses_new_changes(self):
        with tempfile.TemporaryDirectory(dir=core.KIT) as temporary:
            root=Path(temporary); original=root/'settings.json'; saved=root/'saved.bak'
            original.write_text('installed',encoding='utf-8'); saved.write_text('original',encoding='utf-8')
            from core import file_hash
            state={'files':[{'path':str(original),'backup':str(saved),'installed':file_hash(original)}],
                'created':[],'path_before':None}
            core.atomic_json(root/'installation.json',state)
            with patch.object(rollback,'KIT',root):
                original.write_text('new user edit',encoding='utf-8')
                with self.assertRaises(RuntimeError): rollback.rollback()
                self.assertEqual(original.read_text(),'new user edit')
                original.write_text('installed',encoding='utf-8')
                rollback.rollback()
                self.assertEqual(original.read_text(),'original')
    @unittest.skipUnless(os.name == 'nt', 'DPAPI is Windows-only')
    def test_dpapi_roundtrip(self):
        secret=b'synthetic-unit-test-only'
        encrypted=core.dpapi(secret)
        self.assertNotIn(secret,encrypted)
        self.assertEqual(core.dpapi(encrypted,decrypt=True),secret)
    def test_handoff_excludes_thinking_tools_and_token(self):
        with tempfile.TemporaryDirectory(dir=core.KIT) as root:
            home=Path(root); original=home/'.claude'; original.mkdir()
            transcript=original/'test.jsonl'
            records=[{'type':'user','message':{'content':'do work sk-FAKEONLY123456789012345'}},
                {'type':'assistant','message':{'content':[{'type':'thinking','thinking':'PRIVATE REASONING'},{'type':'tool_use','input':{'token':'PRIVATE TOOL'}},{'type':'text','text':'next step'}]}}]
            transcript.write_text('\n'.join(json.dumps(r) for r in records),encoding='utf-8')
            state=launcher.Activity(); state.transcript=str(transcript); state.cwd=root
            with patch.object(launcher,'HOME',home):
                handoff=launcher.handoff(state,home)
            output=handoff.read_text(encoding='utf-8')
            self.assertNotIn('PRIVATE REASONING',output)
            self.assertNotIn('PRIVATE TOOL',output)
            self.assertNotIn('sk-FAKE',output)
            self.assertIn('next step',output)
    def test_native_process_shutdown_at_idle_boundary(self):
        # Actual Windows process group; no real Claude, credential or API call.
        child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'],creationflags=getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0))
        try:
            time.sleep(.2)
            try:
                child.send_signal(getattr(signal, 'CTRL_BREAK_EVENT', signal.SIGTERM))
            except OSError:
                # Tool hosts may have no Windows console; supervisor has the same safe fallback.
                child.terminate()
            child.wait(timeout=5)
            self.assertIsNotNone(child.returncode)
        finally:
            if child.poll() is None: child.terminate(); child.wait(timeout=5)

    def test_complete_automatic_transfer_with_real_fake_child(self):
        # Real native process, real hook, real shutdown and textual handoff; router is mocked.
        with tempfile.TemporaryDirectory(dir=core.KIT) as temporary:
            root=Path(temporary); original=root/'.claude'; original.mkdir(); run=root/'run'; run.mkdir()
            transcript=original/'test.jsonl'
            transcript.write_text(json.dumps({'type':'user','message':{'content':'continue fixture task'}})+'\n',encoding='utf-8')
            script=root/'fake_native.py'
            script.write_text('import json,os,subprocess,sys,time\n' +
                'event={"hook_event_name":"StopFailure","error":"rate_limit","last_assistant_message":"weekly usage limit exceeded","session_id":"test","cwd":'+repr(str(root))+',"transcript_path":'+repr(str(transcript))+'}\n'+
                'subprocess.run([sys.executable,'+repr(str(core.KIT/'runtime/hook.py'))+'],input=json.dumps(event).encode(),env=os.environ)\n'+
                'time.sleep(30)\n',encoding='utf-8')
            holder={}
            def start(args,env):
                child=subprocess.Popen([sys.executable,str(script)],env=env,creationflags=getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0))
                holder['child']=child
                return child
            def router(args,run,continuity):
                self.assertIsNotNone(holder['child'].poll())
                self.assertIn('continue fixture task',continuity.read_text(encoding='utf-8'))
                return 0
            with patch.object(launcher,'HOME',root),patch.object(launcher,'start_native',start),patch.object(launcher,'run_router',router) as mocked:
                self.assertEqual(launcher.run_original([],run),0)
            self.assertTrue((run/'transferencia.json').exists())
            self.assertTrue(core.read_json(run/'transferencia.json')['automatic'])

if __name__=='__main__':
    import sys
    unittest.main(verbosity=2)
