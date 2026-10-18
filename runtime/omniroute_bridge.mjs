// Local management uses the shipped OmniRoute API client and its machine credential.
// stdout is captured privately by Python; never run this bridge with terminal output.
import { readFile, writeFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
try {
  let input=''; for await(const chunk of process.stdin) input+=chunk;
  const config=JSON.parse(input);
  if(config.url!=='http://127.0.0.1:20128') throw new Error('loopback only');
  const {apiFetch}=await import(pathToFileURL(join(config.package,'bin/cli/api.mjs')).href);
  async function api(path,method='GET',body){
    const r=await apiFetch(path,{baseUrl:config.url,method,body,retry:false,acceptNotOk:true,timeout:20000});
    if(!r.ok)throw new Error('HTTP '+r.status);
    return r.json();
  }
  const providers=await api('/api/providers?limit=5000');
  const connections=(providers.connections||[]).filter(c=>c.provider==='openrouter' && c.isActive);
  if(!connections.some(c=>c.name==='main1'))throw new Error('main1 required');
  for(const name of ['main1','main2'])if(connections.filter(c=>c.name===name).length>1)throw new Error('ambiguous account name');
  const settings=await api('/api/settings');
  const before={providerStrategies:settings.providerStrategies||{},connections:connections.map(c=>({id:c.id,name:c.name,priority:c.priority})),created_key_id:null};
  await writeFile(config.backup,JSON.stringify(before,null,2),{mode:0o600});
  const strategies={...before.providerStrategies,openrouter:{...(before.providerStrategies.openrouter||{}),fallbackStrategy:'fill-first'}};
  if(JSON.stringify(strategies)!==JSON.stringify(before.providerStrategies))await api('/api/settings','PATCH',{providerStrategies:strategies});
  for(const c of connections){
    const rank=c.name==='main1'?1:c.name==='main2'?2:Math.max(3,c.priority||3);
    if(c.priority!==rank)await api('/api/providers/'+encodeURIComponent(c.id),'PUT',{priority:rank});
  }
  let secret, key_id;
  if(config.createKey){
    const created=await api('/api/keys','POST',{name:'Claude Antigravity Kit '+Date.now(),modelAccessMode:'restricted',allowedModels:config.models,allowedCombos:[]});
    const key=typeof created.key==='object'?created.key:created;
    secret=typeof created.key==='string'?created.key:key.key||key.apiKey||created.apiKey;
    key_id=key.id||created.id;
    before.created_key_id=key_id;
    await writeFile(config.backup,JSON.stringify(before,null,2),{mode:0o600});
    if(!secret)throw new Error('missing key');
  }
  const verified=await api('/api/settings');
  if(verified.providerStrategies?.openrouter?.fallbackStrategy!=='fill-first')throw new Error('strategy verification');
  const rows=(await api('/api/providers?limit=5000')).connections.filter(c=>c.provider==='openrouter'&&c.isActive);
  if(rows.find(c=>c.name==='main1')?.priority!==1 || (rows.some(c=>c.name==='main2')&&rows.find(c=>c.name==='main2').priority!==2))throw new Error('priority verification');
  process.stdout.write(JSON.stringify({secret,key_id,connections:rows.map(c=>({id:c.id,name:c.name,priority:c.priority})),strategy:'fill-first'}));
}catch{process.stderr.write('OmniRoute pool setup failed.\n');process.exitCode=1;}
