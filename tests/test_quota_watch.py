import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
import core
import launcher
import quota_watch as q

class QuotaWatchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.event={'hook_event_name':'PostToolUse','session_id':'fixture'}
    def tearDown(self):self.temp.cleanup()
    def telemetry(self, used=95, **extra):
        data={'session_id':'fixture','rate_limits':{'seven_day':{'used_percentage':used,'resets_at':time.time()+3600}},**extra}
        q.record(data,self.root)
    def test_missing_expired_wrong_session_and_context_are_not_quota(self):
        for data in ({'session_id':'fixture','context_window':{'used_percentage':99}},
                     {'session_id':'fixture','rate_limits':{'five_hour':{'used_percentage':99,'resets_at':time.time()-1}}},
                     {'session_id':'other','rate_limits':{'seven_day':{'used_percentage':99,'resets_at':time.time()+3600}}}):
            q.record(data,self.root)
            self.assertEqual(q.feedback(self.root,self.event),(None,False))
        self.telemetry(94.9);self.assertFalse(q.approaching(self.root,'fixture'))
        self.telemetry();data=core.read_json(self.root/'quota-telemetry.json');data['time']-=181
        core.atomic_json(self.root/'quota-telemetry.json',data)
        self.assertFalse(q.approaching(self.root,'fixture'))
    def test_transfer_requires_prepared_checkpoint_normal_stop_and_no_background(self):
        self.telemetry();text,ready=q.feedback(self.root,self.event)
        self.assertIn('95%',text);self.assertFalse(ready)
        self.assertEqual(q.feedback(self.root,self.event),(None,False))
        (self.root/'quota-decision.json').write_text('{unfinished',encoding='utf-8')
        self.assertEqual(q.feedback(self.root,self.event),(None,False))
        core.atomic_json(self.root/'quota-decision.json',{'session_id':'fixture','action':'transfer'})
        stop={**self.event,'hook_event_name':'Stop'}
        self.assertFalse(q.feedback(self.root,stop)[1])
        (self.root/'HANDOFF.md').write_text('Verified checkpoint',encoding='utf-8')
        self.assertTrue(q.feedback(self.root,stop)[1])
        self.assertFalse(q.feedback(self.root,{**stop,'background_tasks':[{'id':'active'}]})[1])
        self.assertFalse(q.feedback(self.root,{**stop,'session_crons':[{'id':'active'}]})[1])
        self.assertFalse(q.feedback(self.root,{**stop,'agent_id':'child'})[1])
    def test_completed_task_does_not_transfer_or_loop_and_new_prompt_resets(self):
        self.telemetry();q.feedback(self.root,self.event)
        stop={**self.event,'hook_event_name':'Stop'}
        self.assertTrue(q.feedback(self.root,stop)[0])
        self.assertEqual(q.feedback(self.root,stop),(None,False))
        core.atomic_json(self.root/'quota-decision.json',{'session_id':'fixture','action':'complete'})
        self.assertEqual(q.feedback(self.root,stop),(None,False))
        q.feedback(self.root,{**self.event,'hook_event_name':'UserPromptSubmit'})
        self.assertFalse((self.root/'quota-request.json').exists())
    def test_refresh_does_not_make_old_quota_fresh_and_new_turn_cancels_closure(self):
        data={'session_id':'fixture','rate_limits':{'seven_day':{'used_percentage':96,'resets_at':time.time()+3600}}}
        q.record(data,self.root)
        snapshot=core.read_json(self.root/'quota-telemetry.json');snapshot['time']-=181
        core.atomic_json(self.root/'quota-telemetry.json',snapshot)
        q.record(data,self.root)
        self.assertFalse(q.approaching(self.root,'fixture'))
        state=launcher.Activity();state.consume({'event':'Stop','quota':True})
        self.assertTrue(state.idle());self.assertIsNotNone(state.quota)
        state.consume({'event':'UserPromptSubmit'})
        self.assertFalse(state.idle());self.assertIsNone(state.quota)

    def test_statusline_records_only_quota_and_preserves_custom_output(self):
        core.atomic_json(self.root/'previous-statusline.json',{'type':'command','command':'echo preserved-status'})
        data={'session_id':'fixture','rate_limits':{'seven_day':{'used_percentage':96,'resets_at':time.time()+3600}},'secret':'must-not-persist'}
        env={**os.environ,'CLAUDE_PERFIS_RUN':str(self.root)}
        result=subprocess.run([sys.executable,q.__file__],input=json.dumps(data),text=True,capture_output=True,env=env)
        self.assertEqual(result.returncode,0);self.assertIn('preserved-status',result.stdout)
        self.assertNotIn('must-not-persist',(self.root/'quota-telemetry.json').read_text())
    def test_proactive_stop_event_requires_checkpoint_and_idle_state(self):
        self.telemetry();q.feedback(self.root,self.event)
        (self.root/'HANDOFF.md').write_text('Checkpoint fixture',encoding='utf-8')
        core.atomic_json(self.root/'quota-decision.json',{'session_id':'fixture','action':'transfer'})
        event={**self.event,'hook_event_name':'Stop','cwd':str(self.root),'transcript_path':'fixture'}
        env={**os.environ,'CLAUDE_PERFIS_RUN':str(self.root),'CLAUDE_PERFIS_PROFILE':'original'}
        result=subprocess.run([sys.executable,str(Path(q.__file__).with_name('hook.py'))],input=json.dumps(event),text=True,capture_output=True,env=env)
        self.assertEqual(result.returncode,0)
        state=launcher.Activity()
        state.consume(core.read_json(next(self.root.glob('*.event.json'))))
        self.assertEqual(state.quota['reason'],'anthropic_proactive_95');self.assertTrue(state.idle())
        state.consume({'event':'SubagentStart','agent':'still-running'})
        self.assertFalse(state.idle())
    def test_supervisor_transfers_after_prepared_95_checkpoint(self):
        original=self.root/'.claude';original.mkdir();run=self.root/'run';run.mkdir()
        transcript=original/'fixture.jsonl'
        transcript.write_text(json.dumps({'type':'user','message':{'content':'Finish pending synthetic task'}})+'\n',encoding='utf-8')
        script=self.root/'fake_native.py'
        script.write_text("import json,os,sys,subprocess,time\nfrom pathlib import Path\n"
            +"root=Path(os.environ['CLAUDE_PERFIS_RUN'])\n"
            +"core="+repr(str(Path(q.__file__).parent))+"\nsys.path.insert(0,core)\nimport quota_watch as q\n"
            +"q.record({'session_id':'fixture','rate_limits':{'seven_day':{'used_percentage':95,'resets_at':time.time()+3600}}},root)\n"
            +"event="+repr({'hook_event_name':'Stop','session_id':'fixture','cwd':str(self.root),'transcript_path':str(transcript)})+"\n"
            +"def hook():\n return subprocess.run([sys.executable,str(Path(core)/'hook.py')],input=json.dumps(event),text=True,capture_output=True)\n"
            +"first=hook();assert 'additionalContext' in first.stdout\n"
            +"(root/'HANDOFF.md').write_text('Pending: run the final fixture verification.',encoding='utf-8')\n"
            +"(root/'quota-decision.json').write_text(json.dumps({'session_id':'fixture','action':'transfer'}))\n"
            +"hook()\ntime.sleep(30)\n",encoding='utf-8')
        def start(args,env):
            return subprocess.Popen([sys.executable,str(script)],env=env,creationflags=getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0))
        def router(args,run,continuity):
            self.assertIn('Pending: run the final fixture verification.',continuity.read_text(encoding='utf-8'))
            self.assertIn('Finish pending synthetic task',continuity.read_text(encoding='utf-8'))
            return 0
        with patch.object(launcher,'HOME',self.root),patch.object(launcher,'start_native',start),patch.object(launcher,'run_router',side_effect=router) as next_profile:
            self.assertEqual(launcher.run_original([],run),0)
        self.assertEqual(next_profile.call_count,1)
        self.assertEqual(core.read_json(run/'transferencia.json')['reason'],'anthropic_proactive_95')

    def test_bridge_orders_fifteen_accounts_numerically_and_is_idempotent(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node required')
        package=self.root/'package';(package/'bin/cli').mkdir(parents=True)
        state={'connections':[{'id':str(i),'provider':'openrouter','name':'main'+str(i),'isActive':True,'priority':1} for i in range(15,0,-1)],'settings':{},'writes':0}
        file=self.root/'state.json';core.atomic_json(file,state)
        (package/'bin/cli/api.mjs').write_text(
            "import fs from 'node:fs'; const p=process.env.FIXTURE_STATE; export async function apiFetch(path,o){let s=JSON.parse(fs.readFileSync(p));let data;if(o.method==='GET'){data=path.startsWith('/api/providers?')?{connections:s.connections}:s.settings;}else{ s.writes++; if(o.method==='PATCH')Object.assign(s.settings,o.body);else Object.assign(s.connections.find(c=>c.id===path.split('/').pop()),o.body);fs.writeFileSync(p,JSON.stringify(s));data={};}return {ok:true,json:async()=>data};}",encoding='utf-8')
        request={'url':'http://127.0.0.1:20128','package':str(package),'backup':str(self.root/'backup.json'),'createKey':False}
        bridge=Path(q.__file__).with_name('omniroute_bridge.mjs')
        env={**os.environ,'FIXTURE_STATE':str(file)}
        for attempt in range(2):
            result=subprocess.run([node,str(bridge)],input=json.dumps(request),text=True,capture_output=True,env=env)
            self.assertEqual(result.returncode,0,result.stderr)
            data=core.read_json(file)
            self.assertTrue(all(c['priority']==int(c['name'][4:]) for c in data['connections']))
            if attempt==0:writes=data['writes']
            else:self.assertEqual(data['writes'],writes)

if __name__=='__main__':unittest.main()
