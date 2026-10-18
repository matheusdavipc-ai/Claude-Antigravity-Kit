import http.client
import json
import socket
import sys
import threading
import tempfile
import subprocess
import os
from unittest.mock import patch
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
import core
import launcher
import gateway
import omniroute_pool

class Pool(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        self.send_response(200);self.end_headers();self.wfile.write(b'{"status":"ok"}')
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.requests.append((self.path,body,self.headers.get('Authorization')))
        # A local protocol double of OmniRoute: account fallback happens inside one HTTP call.
        for account in ('main1','main2'):
            self.server.accounts.append((account,body['model']))
            status=self.server.statuses.get((account,body['model']),200)
            if status==429 and account=='main1': continue
            self.send_response(status)
            self.send_header('Content-Type','application/json')
            self.send_header('X-OmniRoute-Selected-Connection-Id',account)
            self.end_headers()
            self.wfile.write(json.dumps({'content':[{'type':'text','text':'synthetic fixture'}]}).encode())
            break

class OmniRouteTests(unittest.TestCase):
    def setUp(self):
        self.pool=ThreadingHTTPServer(('127.0.0.1',0),Pool)
        self.pool.requests=[];self.pool.accounts=[];self.pool.statuses={}
        threading.Thread(target=self.pool.serve_forever,daemon=True).start()
        catalog={m:{'free':True,'tools':True,'modalities':['text','image'],'context':1000000,'max_output':65536,'expires':None} for m in core.MODELS}
        self.gate=gateway.Gateway('synthetic-local-key',catalog,f'http://127.0.0.1:{self.pool.server_port}')
        threading.Thread(target=self.gate.serve_forever,daemon=True).start()
    def tearDown(self):
        self.gate.shutdown();self.gate.server_close();self.pool.shutdown();self.pool.server_close()
    def request(self,**extra):
        c=http.client.HTTPConnection('127.0.0.1',self.gate.server_port,timeout=5)
        body={'model':'router-fast','max_tokens':2,'messages':[{'role':'user','content':'fixture'}],**extra}
        c.request('POST','/v1/messages',json.dumps(body),{'Authorization':'Bearer '+self.gate.token})
        r=c.getresponse();status=r.status;r.read();c.close();return status
    def test_main1_quota_uses_main2_before_model_reserve(self):
        principal='openrouter/'+core.ROLES['router-fast'][0]
        self.pool.statuses[('main1',principal)]=429
        self.assertEqual(self.request(),200)
        self.assertEqual(self.pool.accounts,[('main1',principal),('main2',principal)])
        self.assertEqual(len(self.pool.requests),1)
        self.assertEqual(self.pool.requests[0][0],'/v1/messages')
        self.assertEqual(self.pool.requests[0][2],'Bearer synthetic-local-key')
        self.assertEqual(self.gate.events[-1]['connection_id'],'main2')
    def test_exhausted_pool_only_then_uses_prescribed_model_reserve(self):
        principal='openrouter/'+core.ROLES['router-fast'][0]
        reserve='openrouter/'+core.ROLES['router-fast'][1]
        for account in ('main1','main2'):self.pool.statuses[(account,principal)]=429
        self.assertEqual(self.request(),200)
        self.assertEqual([r[1]['model'] for r in self.pool.requests],[principal,reserve])
    def test_caller_cannot_pin_an_account_or_change_provider(self):
        self.assertEqual(self.request(provider={'only':['other']},models=['paid'],route='fallback'),200)
        body=self.pool.requests[0][1]
        for field in ('provider','models','route'):self.assertNotIn(field,body)
        self.assertTrue(body['model'].startswith('openrouter/'))
    def test_auth_failure_does_not_replay(self):
        self.pool.statuses[('main1','openrouter/'+core.ROLES['router-fast'][0])]=401
        self.assertEqual(self.request(),401)
        self.assertEqual(len(self.pool.requests),1)
    def test_external_gateway_blocked(self):
        for url in ('https://openrouter.ai','http://example.com','http://127.0.0.1:20128/other'):
            with self.assertRaises(ValueError):gateway.Gateway('fixture',{},url)
    def test_unavailable_server_has_actionable_error(self):
        sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
        with self.assertRaisesRegex(RuntimeError,'Execute omniroute'):
            omniroute_pool.require_ready(f'http://127.0.0.1:{port}')

    def test_subscription_handoff_continues_via_omniroute_main2(self):
        principal='openrouter/'+core.ROLES['router-fast'][0]
        self.pool.statuses[('main1',principal)]=429
        with tempfile.TemporaryDirectory() as temp:
            home=Path(temp);original=home/'.claude';original.mkdir();run=home/'run';run.mkdir();router=home/'router';router.mkdir()
            transcript=original/'fixture.jsonl'
            transcript.write_text(json.dumps({'type':'user','message':{'content':'continue synthetic fixture'}})+'\n',encoding='utf-8')
            core.atomic_json(router/'upstream.json',{'url':f'http://127.0.0.1:{self.pool.server_port}'})
            script=home/'native_fixture.py'
            event={'hook_event_name':'StopFailure','error':'rate_limit','last_assistant_message':'weekly usage limit exceeded','session_id':'fixture','cwd':str(home),'transcript_path':str(transcript)}
            script.write_text('import os,sys,json,subprocess,time,urllib.request\n'
                +'if os.environ["CLAUDE_PERFIS_PROFILE"]=="original":\n'
                +' subprocess.run([sys.executable,'+repr(str(core.KIT/'runtime/hook.py'))+'],input='+repr(json.dumps(event))+'.encode(),env=os.environ)\n'
                +' time.sleep(30)\n'
                +'else:\n'
                +' data=json.dumps({"model":"cohere/north-mini-code:free","max_tokens":2,"messages":[{"role":"user","content":"fixture"}]}).encode()\n'
                +' req=urllib.request.Request(os.environ["ANTHROPIC_BASE_URL"]+"/v1/messages",data=data,headers={"Authorization":"Bearer "+os.environ["ANTHROPIC_AUTH_TOKEN"],"Content-Type":"application/json"})\n'
                +' with urllib.request.urlopen(req,timeout=10) as response: assert response.status==200\n',encoding='utf-8')
            def start(args,env):
                return subprocess.Popen([sys.executable,str(script)],env=env,creationflags=getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0))
            with patch.object(launcher,'HOME',home),patch.object(launcher,'ROUTER',router),patch.object(launcher,'start_native',start),patch.object(launcher,'load_secret',return_value='synthetic-local-key'),patch.object(gateway,'get_catalog',return_value=self.gate.catalog):
                self.assertEqual(launcher.run_original([],run),0)
            self.assertTrue(core.read_json(run/'transferencia.json')['automatic'])
            handoff=Path(core.read_json(run/'transferencia.json')['handoff'])
            self.assertIn('continue synthetic fixture',handoff.read_text(encoding='utf-8'))
            self.assertEqual(core.read_json(run/'modelos-utilizados.json')[-1]['connection_id'],'main2')
